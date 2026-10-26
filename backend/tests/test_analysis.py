from datetime import time

import pandas as pd

from app.analysis import decision_forecasts, mae_by_horizon, summarize, with_actuals


def ts(s):
    return pd.Timestamp(s, tz="UTC")


def forecasts(*rows):
    """rows of (publish_time, start_time, generation_mw)."""
    df = pd.DataFrame(rows, columns=["publish_time", "start_time", "generation_mw"])
    df["publish_time"] = pd.to_datetime(df["publish_time"], utc=True)
    df["start_time"] = pd.to_datetime(df["start_time"], utc=True)
    df["horizon_h"] = (df["start_time"] - df["publish_time"]).dt.total_seconds() / 3600
    return df


TARGET = "2026-01-15T18:00:00Z"
DAY_BEFORE_BATCHES = forecasts(
    ("2026-01-14T04:30:00Z", TARGET, 8800),
    ("2026-01-14T07:30:00Z", TARGET, 8962),
    ("2026-01-14T09:30:00Z", TARGET, 9053),
)


class TestDecisionForecasts:
    def test_picks_latest_forecast_before_auction(self):
        row = decision_forecasts(DAY_BEFORE_BATCHES).iloc[0]
        assert row["publish_time"] == ts("2026-01-14T07:30:00Z")
        assert row["generation_mw"] == 8962
        assert not row["stale"]

    def test_later_cutoff_picks_later_forecast(self):
        # If the auction moved to 11:00, the 09:30 forecast becomes usable.
        row = decision_forecasts(DAY_BEFORE_BATCHES, cutoff=time(11, 0)).iloc[0]
        assert row["publish_time"] == ts("2026-01-14T09:30:00Z")

    def test_missing_publish_falls_back_and_is_flagged_stale(self):
        without_0730 = DAY_BEFORE_BATCHES.drop(index=1)
        row = decision_forecasts(without_0730).iloc[0]
        assert row["publish_time"] == ts("2026-01-14T04:30:00Z")
        assert row["stale"]

    def test_hour_without_any_usable_forecast_is_left_out(self):
        too_late = forecasts(("2026-01-14T09:30:00Z", TARGET, 9053))
        assert decision_forecasts(too_late).empty

    def test_cutoff_is_uk_local_time_in_summer(self):
        # 09:00 BST = 08:00 UTC, so a forecast published at 08:30 UTC is too late in July.
        batches = forecasts(
            ("2026-07-14T07:30:00Z", "2026-07-15T18:00:00Z", 5000),
            ("2026-07-14T08:30:00Z", "2026-07-15T18:00:00Z", 5100),
        )
        row = decision_forecasts(batches).iloc[0]
        assert row["publish_time"] == ts("2026-07-14T07:30:00Z")


def test_error_is_forecast_minus_actual_on_the_hour():
    actuals = pd.DataFrame(
        {"start_time": [ts(TARGET), ts("2026-01-15T18:30:00Z")], "generation_mw": [7000, 7100]}
    )
    matched = with_actuals(forecasts(("2026-01-14T07:30:00Z", TARGET, 9000)), actuals)
    assert matched["actual_mw"].tolist() == [7000]
    assert matched["error_mw"].tolist() == [2000]  # forecast too high: buyer is short


def test_summarize():
    stats = summarize(pd.Series([100.0, -100.0, 300.0]))
    assert stats["count"] == 3
    assert stats["mae"] == 166.7  # 500 / 3, rounded
    assert stats["bias"] == 100


def test_percentiles_bracket_80_percent_of_errors():
    stats = summarize(pd.Series(range(0, 101), dtype=float))
    assert (stats["p10"], stats["p50"], stats["p90"]) == (10, 50, 90)


def test_mae_by_horizon_buckets():
    matched = pd.DataFrame({"horizon_h": [3.0, 5.0, 20.0], "error_mw": [-100.0, 300.0, 1000.0]})
    out = mae_by_horizon(matched, [0, 6, 24])
    assert out.to_dict("records") == [
        {"from_h": 0, "to_h": 6, "mae": 200.0, "count": 2},
        {"from_h": 6, "to_h": 24, "mae": 1000.0, "count": 1},
    ]
