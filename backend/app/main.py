"""HTTP API. The data (~2 MB) is loaded once per process and kept in memory."""

import asyncio
import logging
import time as clock
from contextlib import asynccontextmanager
from datetime import date, datetime, time
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request

from app import analysis, auth
from app.data import Datasets, load_datasets
from app.schemas import (
    ActualPoint,
    DayDetail,
    DaySummary,
    ErrorDistribution,
    ErrorSummary,
    ForecastHistory,
    Health,
    HorizonBucket,
)
from app.utils import to_utc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")

HORIZON_EDGES = [0, 6, 12, 18, 24, 36, 48, 72]


async def _ensure_data(app: FastAPI) -> Datasets:
    """Load the datasets once per process. Concurrent first requests share the same load."""
    if app.state.data is None:
        async with app.state.load_lock:
            if app.state.data is None:
                app.state.data = await app.state.loader()
                log.info(
                    "Loaded %d actuals, %d forecasts",
                    len(app.state.data.actuals),
                    len(app.state.data.forecasts),
                )
    return app.state.data


async def get_data(request: Request) -> Datasets:
    """The shared datasets: loaded at startup, or by the first request where a host
    (e.g. a serverless platform) doesn't run startup hooks."""
    return await _ensure_data(request.app)


Data = Annotated[Datasets, Depends(get_data)]

public = APIRouter(prefix="/api/v1")
# Every route on this router requires a logged-in user.
router = APIRouter(prefix="/api/v1", dependencies=[Depends(auth.require_user)])


@public.get("/health")
def health(data: Data) -> Health:
    return Health(status="ok", actual_rows=len(data.actuals), forecast_rows=len(data.forecasts))


@router.get("/actuals")
def actuals(
    data: Data, start: datetime | None = None, end: datetime | None = None
) -> list[ActualPoint]:
    """Half-hourly actual wind generation, optionally limited to start <= start_time < end."""
    df = data.actuals
    if start:
        df = df[df["start_time"] >= to_utc(start)]
    if end:
        df = df[df["start_time"] < to_utc(end)]
    return df.to_dict("records")


Cutoff = Annotated[
    time,
    Query(description="Market (UK) local time on the day before delivery: the auction deadline"),
]
DEFAULT_CUTOFF = time(9, 0)


def _decision_hours(data: Datasets, cutoff: time) -> pd.DataFrame:
    """Every hour's forecast available at the cutoff, joined to its actual."""
    chosen = analysis.decision_forecasts(data.forecasts, cutoff)
    matched = analysis.with_actuals(chosen, data.actuals)
    if matched.empty:
        raise HTTPException(404, "No forecasts were published before this cutoff")
    return matched.rename(columns={"generation_mw": "forecast_mw"})


@router.get("/accuracy/summary")
def accuracy_summary(data: Data, cutoff: Cutoff = DEFAULT_CUTOFF) -> ErrorSummary:
    """Headline accuracy of the forecasts available at the cutoff, over all hours."""
    return ErrorSummary(**analysis.summarize(_decision_hours(data, cutoff)["error_mw"]))


@router.get("/accuracy/distribution")
def accuracy_distribution(data: Data, cutoff: Cutoff = DEFAULT_CUTOFF) -> ErrorDistribution:
    """Histogram of errors, and the share of hours still short for each safety margin."""
    errors = _decision_hours(data, cutoff)["error_mw"]
    return ErrorDistribution(
        bins=analysis.error_histogram(errors).to_dict("records"),
        shortfall=analysis.shortfall_curve(errors).to_dict("records"),
    )


@router.get("/days")
def days(data: Data, cutoff: Cutoff = DEFAULT_CUTOFF) -> list[DaySummary]:
    """Every delivery day with its typical miss (mean absolute error)."""
    return analysis.mae_by_day(_decision_hours(data, cutoff)).to_dict("records")


@router.get("/days/{day}")
def day_detail(data: Data, day: date, cutoff: Cutoff = DEFAULT_CUTOFF) -> DayDetail:
    """One market (UK) day: each hour's forecast at the cutoff vs actual, and all actuals."""
    start, end = analysis.market_day_bounds(day)
    hours = _decision_hours(data, cutoff)
    hours = hours[(hours["start_time"] >= start) & (hours["start_time"] < end)]
    if hours.empty:
        raise HTTPException(404, f"No data for {day}")
    actuals = data.actuals
    actuals = actuals[(actuals["start_time"] >= start) & (actuals["start_time"] < end)]
    return DayDetail(
        date=day,
        mae=round(float(hours["error_mw"].abs().mean()), 1),
        hours=hours.to_dict("records"),
        actuals=actuals.to_dict("records"),
    )


@router.get("/forecasts")
def forecast_history(data: Data, start_time: datetime) -> ForecastHistory:
    """Every forecast ever published for one target hour, oldest first."""
    target = to_utc(start_time)
    rows = data.forecasts[data.forecasts["start_time"] == target].sort_values("publish_time")
    if rows.empty:
        raise HTTPException(404, "No forecasts for this time. Forecasts are hourly (e.g. 18:00).")
    actual = data.actuals.loc[data.actuals["start_time"] == target, "generation_mw"]
    return ForecastHistory(
        start_time=target,
        actual_mw=float(actual.iloc[0]) if not actual.empty else None,
        forecasts=rows.rename(columns={"generation_mw": "forecast_mw"}).to_dict("records"),
    )


@router.get("/accuracy/by-horizon")
def accuracy_by_horizon(data: Data) -> list[HorizonBucket]:
    """Mean absolute error of all forecasts, grouped by how far ahead they were made."""
    matched = analysis.with_actuals(data.forecasts, data.actuals)
    return analysis.mae_by_horizon(matched, HORIZON_EDGES).to_dict("records")


def create_app(loader=load_datasets) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await _ensure_data(app)  # load before the first request arrives
        yield

    app = FastAPI(
        title="Wind Forecast API",
        version="1.0.0",
        lifespan=lifespan,
        # Under /api, so the docs are reachable wherever only /api/* reaches the backend
        # (Vercel rewrites, nginx in Docker).
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )
    app.state.loader = loader
    app.state.data = None
    app.state.load_lock = asyncio.Lock()

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started = clock.perf_counter()
        response = await call_next(request)
        elapsed_ms = (clock.perf_counter() - started) * 1000
        log.info(
            "%s %s -> %d (%.0f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    app.include_router(auth.router)
    app.include_router(public)
    app.include_router(router)
    return app


app = create_app()
