"""Turn raw Elexon rows into tidy DataFrames with UTC timestamps."""

import pandas as pd


def clean_actuals(rows: list[dict]) -> pd.DataFrame:
    """Half-hourly wind actuals with columns start_time, generation_mw.

    One row per start_time. If a period was republished, the latest publication wins.
    """
    raw = pd.DataFrame(rows, columns=["fuelType", "startTime", "publishTime", "generation"])
    raw = raw[raw["fuelType"] == "WIND"]
    df = pd.DataFrame(
        {
            "start_time": pd.to_datetime(raw["startTime"], utc=True),
            "publish_time": pd.to_datetime(raw["publishTime"], utc=True),
            "generation_mw": pd.to_numeric(raw["generation"]),
        }
    ).dropna(subset=["generation_mw"])
    df = df.sort_values("publish_time").drop_duplicates("start_time", keep="last")
    return df.drop(columns="publish_time").sort_values("start_time").reset_index(drop=True)


def clean_forecasts(rows: list[dict]) -> pd.DataFrame:
    """Hourly wind forecasts with columns publish_time, start_time, horizon_h, generation_mw.

    Each publish also restates ~25 hours of the past; those rows (horizon <= 0) are
    not forecasts and are dropped.
    """
    raw = pd.DataFrame(rows, columns=["publishTime", "startTime", "generation"])
    df = pd.DataFrame(
        {
            "publish_time": pd.to_datetime(raw["publishTime"], utc=True),
            "start_time": pd.to_datetime(raw["startTime"], utc=True),
            "generation_mw": pd.to_numeric(raw["generation"]),
        }
    ).dropna(subset=["generation_mw"])
    df["horizon_h"] = (df["start_time"] - df["publish_time"]).dt.total_seconds() / 3600
    df = df[df["horizon_h"] > 0]
    # Unlike actuals, a repeat within one publish has no newer version to prefer, so
    # row order doesn't matter here.
    df = df.drop_duplicates(["publish_time", "start_time"], keep="last")
    columns = ["publish_time", "start_time", "horizon_h", "generation_mw"]
    return df[columns].sort_values(["publish_time", "start_time"]).reset_index(drop=True)
