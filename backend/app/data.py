"""Load the January datasets: fetch from Elexon once, then serve from a disk cache.

January 2026 is history, so cached responses never go stale.
"""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app import elexon
from app.cleaning import clean_actuals, clean_forecasts
from app.config import (
    CACHE_DIR,
    DELIVERY_END,
    DELIVERY_START,
    FORECAST_PUBLISH_FROM,
    FORECAST_PUBLISH_TO,
)

log = logging.getLogger(__name__)


async def load_raw(
    name: str, fetch: Callable[[], Awaitable[list[dict]]], cache_dir: Path
) -> list[dict]:
    path = cache_dir / f"{name}.json"
    if path.exists():
        log.info("Using cached %s", path)
        return json.loads(path.read_text())

    rows = await fetch()
    if not rows:
        # Don't cache an empty answer: it would hide the problem on every later run.
        raise RuntimeError(f"Elexon returned no rows for {name}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows))
    tmp.replace(path)  # atomic, so a crash mid-write never leaves a half-written cache
    return rows


@dataclass(frozen=True)
class Datasets:
    """Cleaned data, loaded once and shared read-only by every request."""

    actuals: pd.DataFrame
    forecasts: pd.DataFrame


async def load_datasets(cache_dir: Path = CACHE_DIR) -> Datasets:
    async with elexon.make_client() as client:
        actual_rows, forecast_rows = await asyncio.gather(
            load_raw(
                "actuals",
                lambda: elexon.fetch_actuals(client, DELIVERY_START, DELIVERY_END),
                cache_dir,
            ),
            load_raw(
                "forecasts",
                lambda: elexon.fetch_forecasts(client, FORECAST_PUBLISH_FROM, FORECAST_PUBLISH_TO),
                cache_dir,
            ),
        )
    return Datasets(actuals=clean_actuals(actual_rows), forecasts=clean_forecasts(forecast_rows))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    data = asyncio.run(load_datasets())
    actuals, forecasts = data.actuals, data.forecasts
    print(
        f"actuals:   {len(actuals)} rows, {actuals.start_time.min()} .. {actuals.start_time.max()}"
    )
    print(f"forecasts: {len(forecasts)} rows, {forecasts.publish_time.nunique()} publishes")
