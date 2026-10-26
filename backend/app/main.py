"""HTTP API. The data (~2 MB) is loaded once at startup and kept in memory."""

import logging
import time as clock
from contextlib import asynccontextmanager
from datetime import datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request

from app import analysis, auth
from app.data import Datasets, load_datasets
from app.schemas import (
    ActualPoint,
    DecisionForecasts,
    ForecastHistory,
    Health,
    HorizonBucket,
)
from app.utils import to_utc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")

HORIZON_EDGES = [0, 6, 12, 18, 24, 36, 48, 72]


def get_data(request: Request) -> Datasets:
    """The datasets loaded at startup, shared by all requests (see lifespan below)."""
    return request.app.state.data


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


@router.get("/decision-forecasts")
def decision_forecasts(
    data: Data,
    cutoff: Annotated[
        time, Query(description="UK local time on the day before delivery (auction deadline)")
    ] = time(9, 0),
) -> DecisionForecasts:
    """For every hour, the forecast available at the cutoff, its actual, and the error."""
    chosen = analysis.decision_forecasts(data.forecasts, cutoff)
    matched = analysis.with_actuals(chosen, data.actuals)
    if matched.empty:
        raise HTTPException(404, "No forecasts were published before this cutoff")
    hours = matched.rename(columns={"generation_mw": "forecast_mw"})
    return DecisionForecasts(
        cutoff=cutoff,
        summary=analysis.summarize(matched["error_mw"]),
        hours=hours.to_dict("records"),
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
        # Runs once at startup; every request then reads this via get_data.
        app.state.data = await loader()
        log.info(
            "Loaded %d actuals, %d forecasts",
            len(app.state.data.actuals),
            len(app.state.data.forecasts),
        )
        yield

    app = FastAPI(title="Wind Forecast API", version="1.0.0", lifespan=lifespan)

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
