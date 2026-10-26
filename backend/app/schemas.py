"""Response shapes for the API. Power values are MW, times are UTC."""

from datetime import datetime, time

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class Health(BaseModel):
    status: str
    actual_rows: int
    forecast_rows: int


class ActualPoint(BaseModel):
    start_time: datetime
    generation_mw: float


class ErrorSummary(BaseModel):
    """Error = forecast - actual. 80% of errors fall between p10 and p90."""

    count: int
    mae: float
    bias: float
    p10: float
    p50: float
    p90: float


class DecisionHour(BaseModel):
    start_time: datetime
    publish_time: datetime
    horizon_h: float
    forecast_mw: float
    actual_mw: float
    error_mw: float
    stale: bool


class DecisionForecasts(BaseModel):
    cutoff: time
    summary: ErrorSummary
    hours: list[DecisionHour]


class ForecastPoint(BaseModel):
    publish_time: datetime
    horizon_h: float
    forecast_mw: float


class ForecastHistory(BaseModel):
    start_time: datetime
    actual_mw: float | None
    forecasts: list[ForecastPoint]


class HorizonBucket(BaseModel):
    from_h: float
    to_h: float
    mae: float
    count: int
