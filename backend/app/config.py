"""Settings for the January 2026 analysis window."""

import os
from datetime import UTC, date, datetime
from pathlib import Path

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

# The GB market's clock: auction deadlines and delivery days are UK local time (GMT/BST).
MARKET_TIMEZONE = "Europe/London"

# Delivery days covered by the analysis (inclusive).
DELIVERY_START = date(2026, 1, 1)
DELIVERY_END = date(2026, 1, 31)

# Forecasts look up to ~66h ahead, so the earliest forecast covering 1 Jan 00:00
# was published on 29 Dec. Start a day earlier for margin.
FORECAST_PUBLISH_FROM = datetime(2025, 12, 28, tzinfo=UTC)
FORECAST_PUBLISH_TO = datetime(2026, 2, 1, tzinfo=UTC)

# Raw API responses are cached here; override with CACHE_DIR. On Vercel (which sets
# VERCEL=1) only /tmp is writable.
_default_cache = (
    Path("/tmp/elexon-cache")
    if os.environ.get("VERCEL")
    else Path(__file__).resolve().parent.parent / "data" / "cache"
)
CACHE_DIR = Path(os.environ.get("CACHE_DIR", _default_cache))
