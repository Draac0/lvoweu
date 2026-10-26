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


def test_decision_forecasts_default_cutoff(client):
    body = client.get("/api/v1/decision-forecasts").json()
    assert body["cutoff"] == "09:00:00"
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
    assert body["summary"]["mae"] == 1290.0


def test_decision_forecasts_custom_cutoff(client):
    body = client.get("/api/v1/decision-forecasts", params={"cutoff": "11:00"}).json()
    assert body["hours"][0]["publish_time"] == "2026-01-14T09:30:00Z"


def test_invalid_cutoff_is_rejected(client):
    assert client.get("/api/v1/decision-forecasts", params={"cutoff": "25:00"}).status_code == 422


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
        response = anonymous.get("/api/v1/decision-forecasts")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not logged in"

    def test_tampered_token_is_rejected(self, client):
        client.headers["Authorization"] += "x"
        assert client.get("/api/v1/decision-forecasts").json()["detail"] == "Invalid token"

    def test_expired_token_is_rejected(self, anonymous):
        expired = jwt.encode(
            {"sub": auth.DEMO_EMAIL, "exp": datetime.now(UTC) - timedelta(minutes=1)},
            auth.SECRET,
            algorithm=auth.ALGORITHM,
        )
        response = anonymous.get(
            "/api/v1/decision-forecasts", headers={"Authorization": f"Bearer {expired}"}
        )
        assert response.json()["detail"] == "Session expired, please log in again"
