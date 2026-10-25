"""Settings for the January 2026 analysis window."""

import os
from datetime import UTC, date, datetime
from pathlib import Path

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

# Delivery days covered by the analysis (inclusive).
DELIVERY_START = date(2026, 1, 1)
DELIVERY_END = date(2026, 1, 31)

# Forecasts look up to ~66h ahead, so the earliest forecast covering 1 Jan 00:00
# was published on 29 Dec. Start a day earlier for margin.
FORECAST_PUBLISH_FROM = datetime(2025, 12, 28, tzinfo=UTC)
FORECAST_PUBLISH_TO = datetime(2026, 2, 1, tzinfo=UTC)

# Raw API responses are cached here. Override with CACHE_DIR (e.g. /tmp on Vercel).
CACHE_DIR = Path(
    os.environ.get("CACHE_DIR", Path(__file__).resolve().parent.parent / "data" / "cache")
)
