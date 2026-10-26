"""Small shared helpers."""

from datetime import datetime

import pandas as pd


def to_utc(dt: datetime) -> pd.Timestamp:
    """Treat times without a timezone as UTC."""
    ts = pd.Timestamp(dt)
    return ts.tz_localize("UTC") if ts.tz is None else ts.tz_convert("UTC")
