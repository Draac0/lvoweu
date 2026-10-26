from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app import auth
from app.cleaning import clean_actuals, clean_forecasts
from app.data import Datasets
from app.main import create_app

TARGET = "2026-01-15T18:00:00Z"


async def fake_loader():
    actuals = clean_actuals(
        [
            {"fuelType": "WIND", "startTime": TARGET, "publishTime": TARGET, "generation": 7672},
            {
                "fuelType": "WIND",
                "startTime": "2026-01-15T18:30:00Z",
                "publishTime": TARGET,
                "generation": 7593,
            },
        ]
    )
    forecasts = clean_forecasts(
        [
            {"publishTime": "2026-01-14T07:30:00Z", "startTime": TARGET, "generation": 8962},
            {"publishTime": "2026-01-14T09:30:00Z", "startTime": TARGET, "generation": 9053},
        ]
    )
    return Datasets(actuals=actuals, forecasts=forecasts)


@pytest.fixture
def anonymous():
    with TestClient(create_app(loader=fake_loader)) as c:  # `with` runs startup loading
        yield c


@pytest.fixture
def client(anonymous):
    credentials = {"email": auth.DEMO_EMAIL, "password": auth.DEMO_PASSWORD}
    token = anonymous.post("/api/v1/auth/login", json=credentials).json()["access_token"]
    anonymous.headers["Authorization"] = f"Bearer {token}"
    return anonymous


def test_health_is_public(anonymous):
    assert anonymous.get("/api/v1/health").json() == {
        "status": "ok",
        "actual_rows": 2,
        "forecast_rows": 2,
    }


def test_actuals_can_be_filtered_by_time(client):
    rows = client.get("/api/v1/actuals", params={"start": "2026-01-15T18:30:00Z"}).json()
    assert rows == [{"start_time": "2026-01-15T18:30:00Z", "generation_mw": 7593.0}]


def test_summary_uses_forecast_available_at_default_cutoff(client):
    # 07:30 forecast (8962) vs actual 7672: too high by 1290 MW.
    body = client.get("/api/v1/accuracy/summary").json()
    assert (body["count"], body["mae"], body["bias"]) == (1, 1290.0, 1290.0)


def test_later_cutoff_uses_later_forecast(client):
    # At 11:00 the 09:30 forecast (9053) is usable: too high by 1381 MW.
    body = client.get("/api/v1/accuracy/summary", params={"cutoff": "11:00"}).json()
    assert body["mae"] == 1381.0


def test_invalid_cutoff_is_rejected(client):
    assert client.get("/api/v1/accuracy/summary", params={"cutoff": "25:00"}).status_code == 422


def test_days_lists_each_day_with_its_typical_miss(client):
    assert client.get("/api/v1/days").json() == [{"date": "2026-01-15", "mae": 1290.0}]


def test_day_detail(client):
    body = client.get("/api/v1/days/2026-01-15").json()
    assert body["date"] == "2026-01-15"
    assert body["mae"] == 1290.0
    assert body["hours"] == [
        {
            "start_time": TARGET,
            "publish_time": "2026-01-14T07:30:00Z",
            "horizon_h": 34.5,
            "forecast_mw": 8962.0,
            "actual_mw": 7672.0,
            "error_mw": 1290.0,
            "stale": False,
        }
    ]
    assert [a["start_time"] for a in body["actuals"]] == [TARGET, "2026-01-15T18:30:00Z"]


def test_day_without_data_is_404(client):
    assert client.get("/api/v1/days/2026-01-16").status_code == 404


def test_distribution_has_histogram_and_shortfall_curve(client):
    body = client.get("/api/v1/accuracy/distribution").json()
    assert body["bins"] == [{"from_mw": 1000.0, "to_mw": 2000.0, "count": 1}]
    # The one error is 1290 MW: short until the margin reaches 1300 MW.
    shortfall = {p["margin_mw"]: p["share_short"] for p in body["shortfall"]}
    assert (shortfall[1200.0], shortfall[1300.0]) == (1.0, 0.0)


def test_forecast_history_lists_every_publish_for_one_hour(client):
    body = client.get("/api/v1/forecasts", params={"start_time": TARGET}).json()
    assert body["actual_mw"] == 7672.0
    assert [f["forecast_mw"] for f in body["forecasts"]] == [8962.0, 9053.0]


def test_forecast_history_for_half_hour_is_404(client):
    response = client.get("/api/v1/forecasts", params={"start_time": "2026-01-15T18:30:00Z"})
    assert response.status_code == 404


def test_accuracy_by_horizon(client):
    buckets = client.get("/api/v1/accuracy/by-horizon").json()
    assert [(b["from_h"], b["to_h"], b["count"]) for b in buckets] == [(24, 36, 2)]


class TestAuth:
    def test_login_with_wrong_password_is_rejected(self, anonymous):
        response = anonymous.post(
            "/api/v1/auth/login", json={"email": auth.DEMO_EMAIL, "password": "nope"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Wrong email or password"

    def test_email_is_case_insensitive(self, anonymous):
        credentials = {"email": auth.DEMO_EMAIL.upper(), "password": auth.DEMO_PASSWORD}
        assert anonymous.post("/api/v1/auth/login", json=credentials).status_code == 200

    def test_data_requires_login(self, anonymous):
        response = anonymous.get("/api/v1/accuracy/summary")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not logged in"

    def test_tampered_token_is_rejected(self, client):
        client.headers["Authorization"] += "x"
        assert client.get("/api/v1/accuracy/summary").json()["detail"] == "Invalid token"

    def test_expired_token_is_rejected(self, anonymous):
        expired = jwt.encode(
            {"sub": auth.DEMO_EMAIL, "exp": datetime.now(UTC) - timedelta(minutes=1)},
            auth.SECRET,
            algorithm=auth.ALGORITHM,
        )
        response = anonymous.get(
            "/api/v1/accuracy/summary", headers={"Authorization": f"Bearer {expired}"}
        )
        assert response.json()["detail"] == "Session expired, please log in again"


def test_data_loads_on_first_request_when_startup_hook_does_not_run():
    # Without `with`, TestClient skips startup, like some serverless hosts.
    calls = []

    async def counting_loader():
        calls.append(1)
        return await fake_loader()

    client = TestClient(create_app(loader=counting_loader))
    assert client.get("/api/v1/health").json()["actual_rows"] == 2
    client.get("/api/v1/health")
    assert len(calls) == 1  # loaded once, then reused
