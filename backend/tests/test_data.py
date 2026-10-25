import json

import pytest

from app.data import load_raw

pytestmark = pytest.mark.anyio

ROWS = [{"startTime": "2026-01-01T00:00:00Z", "generation": 1}]


async def test_fetches_and_writes_cache_when_missing(tmp_path):
    async def fetch():
        return ROWS

    assert await load_raw("actuals", fetch, tmp_path) == ROWS
    assert json.loads((tmp_path / "actuals.json").read_text()) == ROWS


async def test_uses_cache_without_calling_elexon(tmp_path):
    (tmp_path / "actuals.json").write_text(json.dumps(ROWS))

    async def fetch():
        raise AssertionError("should not fetch when cached")

    assert await load_raw("actuals", fetch, tmp_path) == ROWS


async def test_empty_response_is_an_error_and_not_cached(tmp_path):
    async def fetch():
        return []

    with pytest.raises(RuntimeError, match="no rows"):
        await load_raw("actuals", fetch, tmp_path)
    assert not (tmp_path / "actuals.json").exists()
