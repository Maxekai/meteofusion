from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    datetime: datetime
    temperature_c: Optional[float] = None
    humidity_percent: Optional[float] = Field(default=None, ge=0, le=100)
    precipitation_probability: Optional[float] = Field(default=None, ge=0, le=100)
    precipitation_total: Optional[float] = Field(default=None, ge=0)
    precipitation_snow: Optional[float] = Field(default=None, ge=0)
    cloud_cover: Optional[float] = Field(default=None, ge=0)
    wind_speed_kmh: Optional[float] = Field(default=None, ge=0)
    apparent_temperature_c: Optional[float] = Field(default=None)


class ProviderForecast(BaseModel):
    provider: str
    latitude: float
    longitude: float
    timezone: str
    forecast: list[ForecastPoint]


class AggregatedStat(BaseModel):
    min: Optional[float] = None
    avg: Optional[float] = None
    max: Optional[float] = None


class AggregatedHourlyForecastPoint(BaseModel):
    datetime: datetime
    provider_count: int = Field(ge=0)
    temperature_c: AggregatedStat = Field(default_factory=AggregatedStat)
    precipitation_probability: AggregatedStat = Field(default_factory=AggregatedStat)
    precipitation_total: AggregatedStat = Field(default_factory=AggregatedStat)
    precipitation_snow: AggregatedStat = Field(default_factory=AggregatedStat)
    humidity_percent: Optional[float] = None
    cloud_cover: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    apparent_temperature_c: Optional[float] = None
    condition: str


class AggregatedDailyForecastPoint(BaseModel):
    date: date
    provider_count: int = Field(ge=0)
    temperature_min_c: AggregatedStat = Field(default_factory=AggregatedStat)
    temperature_max_c: AggregatedStat = Field(default_factory=AggregatedStat)
    precipitation_total: AggregatedStat = Field(default_factory=AggregatedStat)
    condition: str


class AggregationWindow(BaseModel):
    mode: str
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class DailyAggregationWindow(BaseModel):
    mode: str
    start: Optional[date] = None
    end: Optional[date] = None


class AggregatedForecast(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    days: int = Field(ge=1)
    providers_requested: list[str]
    providers_used: list[str]
    provider_errors: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    hourly_window: AggregationWindow
    daily_window: DailyAggregationWindow
    hourly_forecast: list[AggregatedHourlyForecastPoint]
    daily_forecast: list[AggregatedDailyForecastPoint]
