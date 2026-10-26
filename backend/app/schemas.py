"""Response shapes for the API. Power values are MW, times are UTC."""

from datetime import date, datetime

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
    """One hour: the forecast available at the cutoff, what actually happened, and the miss."""

    start_time: datetime
    publish_time: datetime
    horizon_h: float
    forecast_mw: float
    actual_mw: float
    error_mw: float
    stale: bool


class DaySummary(BaseModel):
    date: date
    mae: float


class DayDetail(BaseModel):
    """One market (UK) delivery day: hourly forecasts vs actuals, plus half-hourly actuals."""

    date: date
    mae: float
    hours: list[DecisionHour]
    actuals: list[ActualPoint]


class HistogramBin(BaseModel):
    from_mw: float
    to_mw: float
    count: int


class ShortfallPoint(BaseModel):
    """Planning for `margin_mw` less wind than forecast, the share of hours still short."""

    margin_mw: float
    share_short: float


class ErrorDistribution(BaseModel):
    bins: list[HistogramBin]
    shortfall: list[ShortfallPoint]


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
