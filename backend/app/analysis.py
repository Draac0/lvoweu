"""Which forecast was usable at decision time, and how wrong forecasts were."""

from datetime import date, time

import numpy as np
import pandas as pd

from app.config import MARKET_TIMEZONE

# Elexon publishes at most 4 hours apart, so an older forecast means a publish was skipped.
STALE_AFTER_H = 4


def market_day(start_time: pd.Series) -> pd.Series:
    """The market (UK) calendar day each UTC time falls on, as naive midnight timestamps."""
    return start_time.dt.tz_convert(MARKET_TIMEZONE).dt.tz_localize(None).dt.normalize()


def market_day_bounds(day: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """UTC [start, end) of a market calendar day. In UK summer (BST): 23:00 to 23:00 UTC."""
    midnight = pd.Timestamp(day)
    start = midnight.tz_localize(MARKET_TIMEZONE).tz_convert("UTC")
    end = (midnight + pd.Timedelta(days=1)).tz_localize(MARKET_TIMEZONE).tz_convert("UTC")
    return start, end


def decision_cutoff(start_time: pd.Series, cutoff: time) -> pd.Series:
    """Cutoff (UTC) for each target hour: `cutoff` market local time on the day before delivery."""
    day_before = market_day(start_time) - pd.Timedelta(days=1)
    cutoff_local = day_before + pd.Timedelta(hours=cutoff.hour, minutes=cutoff.minute)
    return cutoff_local.dt.tz_localize(MARKET_TIMEZONE).dt.tz_convert("UTC")


def decision_forecasts(forecasts: pd.DataFrame, cutoff: time = time(9, 0)) -> pd.DataFrame:
    """For each target hour, the latest forecast published at or before the decision cutoff.

    Adds `stale` = True when that forecast is older than usual (a publish was missed).
    Target hours with no forecast before the cutoff are left out.
    """
    df = forecasts.assign(cutoff=decision_cutoff(forecasts["start_time"], cutoff))
    published_in_time = df[df["publish_time"] <= df["cutoff"]]
    latest_per_hour = published_in_time.sort_values("publish_time").groupby("start_time").tail(1)

    hours_old = (
        latest_per_hour["cutoff"] - latest_per_hour["publish_time"]
    ).dt.total_seconds() / 3600
    chosen = latest_per_hour.assign(stale=hours_old > STALE_AFTER_H).drop(columns="cutoff")
    return chosen.sort_values("start_time").reset_index(drop=True)


def with_actuals(forecasts: pd.DataFrame, actuals: pd.DataFrame) -> pd.DataFrame:
    """Join forecasts to actuals on start_time and add error_mw = forecast - actual.

    Forecasts are hourly and actuals half-hourly, so only on-the-hour actuals match.
    Positive error means the forecast promised more wind than arrived (buyer ends up short).
    """
    actual = actuals.rename(columns={"generation_mw": "actual_mw"})
    df = forecasts.merge(actual, on="start_time", how="inner")
    return df.assign(error_mw=df["forecast_mw"] - df["actual_mw"])


def summarize(errors: pd.Series) -> dict[str, float]:
    """Headline accuracy numbers, all in MW, rounded to 0.1 MW."""
    p10, p50, p90 = np.percentile(errors, [10, 50, 90])
    return {
        "count": int(errors.size),
        "mae": round(float(errors.abs().mean()), 1),
        "bias": round(float(errors.mean()), 1),
        "p10": round(float(p10), 1),
        "p50": round(float(p50), 1),
        "p90": round(float(p90), 1),
    }


def mae_by_horizon(matched: pd.DataFrame, edges: list[float]) -> pd.DataFrame:
    """Mean absolute error per forecast-horizon bucket, e.g. edges [0, 6, 12] -> (0, 6], (6, 12]."""
    buckets = pd.cut(matched["horizon_h"], edges)
    grouped = matched["error_mw"].abs().groupby(buckets, observed=True)
    out = grouped.agg(mae="mean", count="size").reset_index()
    out["from_h"] = [b.left for b in out["horizon_h"]]
    out["to_h"] = [b.right for b in out["horizon_h"]]
    return out[["from_h", "to_h", "mae", "count"]]


def mae_by_day(matched: pd.DataFrame) -> pd.DataFrame:
    """Mean absolute error per market delivery day: columns date, mae."""
    day = market_day(matched["start_time"]).dt.date.rename("date")
    out = matched["error_mw"].abs().groupby(day).mean().round(1).rename("mae")
    return out.reset_index()


def error_histogram(errors: pd.Series, width_mw: float = 1000) -> pd.DataFrame:
    """Count of errors per `width_mw` bucket: columns from_mw, to_mw, count."""
    first_edge = np.floor(errors.min() / width_mw) * width_mw
    last_edge = np.floor(errors.max() / width_mw) * width_mw + width_mw
    edges = np.arange(first_edge, last_edge + width_mw, width_mw)
    counts, _ = np.histogram(errors, bins=edges)
    return pd.DataFrame({"from_mw": edges[:-1], "to_mw": edges[1:], "count": counts})


def shortfall_curve(errors: pd.Series, step_mw: float = 100) -> pd.DataFrame:
    """For each safety margin, the share of hours still short: columns margin_mw, share_short.

    Planning for `margin` MW less wind than forecast leaves you short whenever the
    forecast was too high by more than that (error > margin).
    """
    largest_miss = max(errors.max(), 0)
    margins = np.arange(0, largest_miss + step_mw, step_mw)
    misses = errors.to_numpy()
    share_short = [(misses > margin).mean() for margin in margins]
    return pd.DataFrame({"margin_mw": margins, "share_short": np.round(share_short, 4)})
