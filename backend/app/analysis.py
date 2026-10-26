"""Which forecast was usable at decision time, and how wrong forecasts were."""

from datetime import time

import numpy as np
import pandas as pd

UK = "Europe/London"

# Elexon publishes at most 4 hours apart, so an older forecast means a publish was skipped.
STALE_AFTER_H = 4


def decision_cutoff(start_time: pd.Series, cutoff: time) -> pd.Series:
    """Cutoff (UTC) for each target hour: `cutoff` UK local time on the day before delivery."""
    delivery_day = start_time.dt.tz_convert(UK).dt.tz_localize(None).dt.normalize()
    local = (
        delivery_day - pd.Timedelta(days=1) + pd.Timedelta(hours=cutoff.hour, minutes=cutoff.minute)
    )
    return local.dt.tz_localize(UK).dt.tz_convert("UTC")


def decision_forecasts(forecasts: pd.DataFrame, cutoff: time = time(9, 0)) -> pd.DataFrame:
    """For each target hour, the latest forecast published at or before the decision cutoff.

    Adds `stale` = True when that forecast is older than usual (a publish was missed).
    Target hours with no forecast before the cutoff are left out.
    """
    df = forecasts.assign(cutoff=decision_cutoff(forecasts["start_time"], cutoff))
    df = df[df["publish_time"] <= df["cutoff"]]
    df = df.sort_values("publish_time").groupby("start_time").tail(1)
    age_h = (df["cutoff"] - df["publish_time"]).dt.total_seconds() / 3600
    df = df.assign(stale=age_h > STALE_AFTER_H).drop(columns="cutoff")
    return df.sort_values("start_time").reset_index(drop=True)


def with_actuals(forecasts: pd.DataFrame, actuals: pd.DataFrame) -> pd.DataFrame:
    """Join forecasts to actuals on start_time and add error_mw = forecast - actual.

    Forecasts are hourly and actuals half-hourly, so only on-the-hour actuals match.
    Positive error means the forecast promised more wind than arrived (buyer ends up short).
    """
    actual = actuals.rename(columns={"generation_mw": "actual_mw"})
    df = forecasts.merge(actual, on="start_time", how="inner")
    return df.assign(error_mw=df["generation_mw"] - df["actual_mw"])


def summarize(errors: pd.Series) -> dict[str, float]:
    """Headline accuracy numbers, all in MW."""
    p10, p50, p90 = np.percentile(errors, [10, 50, 90])
    return {
        "count": int(errors.size),
        "mae": float(errors.abs().mean()),
        "bias": float(errors.mean()),
        "p10": float(p10),
        "p50": float(p50),
        "p90": float(p90),
    }


def mae_by_horizon(matched: pd.DataFrame, edges: list[float]) -> pd.DataFrame:
    """Mean absolute error per forecast-horizon bucket, e.g. edges [0, 6, 12] -> (0, 6], (6, 12]."""
    buckets = pd.cut(matched["horizon_h"], edges)
    grouped = matched["error_mw"].abs().groupby(buckets, observed=True)
    out = grouped.agg(mae="mean", count="size").reset_index()
    out["from_h"] = [b.left for b in out["horizon_h"]]
    out["to_h"] = [b.right for b in out["horizon_h"]]
    return out[["from_h", "to_h", "mae", "count"]]
