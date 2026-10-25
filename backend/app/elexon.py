"""Async client for the two Elexon BMRS datasets we use."""

import logging
from datetime import date, datetime

import httpx

from app.config import ELEXON_BASE_URL

log = logging.getLogger(__name__)


def make_client() -> httpx.AsyncClient:
    # retries=3 covers connection failures (DNS, resets), not HTTP error statuses.
    transport = httpx.AsyncHTTPTransport(retries=3)
    return httpx.AsyncClient(base_url=ELEXON_BASE_URL, timeout=30.0, transport=transport)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


async def _get_rows(client: httpx.AsyncClient, path: str, params: dict[str, str]) -> list[dict]:
    response = await client.get(path, params=params)
    response.raise_for_status()
    rows = response.json()
    log.info("Fetched %d rows from %s", len(rows), path)
    return rows


async def fetch_actuals(client: httpx.AsyncClient, start: date, end: date) -> list[dict]:
    """Half-hourly wind generation (FUELHH) for settlement dates start..end inclusive."""
    params = {
        "settlementDateFrom": start.isoformat(),
        "settlementDateTo": end.isoformat(),
        "fuelType": "WIND",
    }
    return await _get_rows(client, "/datasets/FUELHH/stream", params)


async def fetch_forecasts(
    client: httpx.AsyncClient, publish_from: datetime, publish_to: datetime
) -> list[dict]:
    """Hourly wind forecasts (WINDFOR) published between publish_from and publish_to."""
    params = {"publishDateTimeFrom": _iso(publish_from), "publishDateTimeTo": _iso(publish_to)}
    return await _get_rows(client, "/datasets/WINDFOR/stream", params)
