from datetime import UTC, date, datetime

import httpx
import pytest

from app import elexon

pytestmark = pytest.mark.anyio


def mock_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url="https://elexon.test", transport=httpx.MockTransport(handler))


async def test_fetch_actuals_requests_wind_for_date_range():
    seen = {}

    def handler(request: httpx.Request):
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json=[{"startTime": "2026-01-01T00:00:00Z"}])

    async with mock_client(handler) as client:
        rows = await elexon.fetch_actuals(client, date(2026, 1, 1), date(2026, 1, 31))

    assert rows == [{"startTime": "2026-01-01T00:00:00Z"}]
    assert seen["path"] == "/datasets/FUELHH/stream"
    assert seen["params"] == {
        "settlementDateFrom": "2026-01-01",
        "settlementDateTo": "2026-01-31",
        "fuelType": "WIND",
    }


async def test_fetch_forecasts_filters_by_publish_time():
    seen = {}

    def handler(request: httpx.Request):
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json=[])

    async with mock_client(handler) as client:
        await elexon.fetch_forecasts(
            client, datetime(2025, 12, 28, tzinfo=UTC), datetime(2026, 2, 1, tzinfo=UTC)
        )

    assert seen["params"] == {
        "publishDateTimeFrom": "2025-12-28T00:00:00Z",
        "publishDateTimeTo": "2026-02-01T00:00:00Z",
    }


async def test_http_error_is_raised_not_swallowed():
    async with mock_client(lambda request: httpx.Response(503)) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await elexon.fetch_actuals(client, date(2026, 1, 1), date(2026, 1, 1))
