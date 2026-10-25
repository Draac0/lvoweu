import pandas as pd

from app.cleaning import clean_actuals, clean_forecasts


def actual(start, generation, publish="2026-01-15T19:00:00Z", fuel="WIND"):
    return {"fuelType": fuel, "startTime": start, "publishTime": publish, "generation": generation}


def forecast(publish, start, generation):
    return {"publishTime": publish, "startTime": start, "generation": generation}


class TestCleanActuals:
    def test_parses_utc_and_sorts_by_start_time(self):
        df = clean_actuals(
            [actual("2026-01-15T18:30:00Z", 7593), actual("2026-01-15T18:00:00Z", 7672)]
        )
        assert list(df.columns) == ["start_time", "generation_mw"]
        assert df["start_time"].tolist() == [
            pd.Timestamp("2026-01-15T18:00:00Z"),
            pd.Timestamp("2026-01-15T18:30:00Z"),
        ]
        assert str(df["start_time"].dt.tz) == "UTC"

    def test_ignores_other_fuel_types(self):
        df = clean_actuals(
            [actual("2026-01-15T18:00:00Z", 7672), actual("2026-01-15T18:00:00Z", 900, fuel="CCGT")]
        )
        assert df["generation_mw"].tolist() == [7672]

    def test_republished_period_keeps_latest_publication(self):
        df = clean_actuals(
            [
                actual("2026-01-15T18:00:00Z", 7000, publish="2026-01-15T19:00:00Z"),
                actual("2026-01-15T18:00:00Z", 7672, publish="2026-01-15T20:00:00Z"),
            ]
        )
        assert df["generation_mw"].tolist() == [7672]

    def test_drops_missing_generation(self):
        df = clean_actuals([actual("2026-01-15T18:00:00Z", None)])
        assert df.empty

    def test_empty_input_gives_empty_frame_with_columns(self):
        df = clean_actuals([])
        assert df.empty
        assert list(df.columns) == ["start_time", "generation_mw"]


class TestCleanForecasts:
    def test_computes_horizon_in_hours(self):
        df = clean_forecasts([forecast("2026-01-14T07:30:00Z", "2026-01-15T18:00:00Z", 8962)])
        assert df["horizon_h"].tolist() == [34.5]

    def test_drops_rows_about_the_past_or_present(self):
        df = clean_forecasts(
            [
                forecast("2026-01-14T22:30:00Z", "2026-01-14T20:00:00Z", 9000),  # past
                forecast("2026-01-14T22:00:00Z", "2026-01-14T22:00:00Z", 9000),  # horizon 0
                forecast("2026-01-14T22:30:00Z", "2026-01-14T23:00:00Z", 9100),  # future
            ]
        )
        assert df["horizon_h"].tolist() == [0.5]

    def test_duplicate_rows_are_collapsed(self):
        row = forecast("2026-01-14T07:30:00Z", "2026-01-15T18:00:00Z", 8962)
        assert len(clean_forecasts([row, dict(row)])) == 1

    def test_empty_input_gives_empty_frame_with_columns(self):
        df = clean_forecasts([])
        assert df.empty
        assert list(df.columns) == ["publish_time", "start_time", "horizon_h", "generation_mw"]
