from datetime import datetime
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
    dew_point_c: Optional[float] = Field(default=None)
    apparent_temperature_c: Optional[float] = Field(default=None)


class ProviderForecast(BaseModel):
    provider: str
    latitude: float
    longitude: float
    timezone: str
    forecast: list[ForecastPoint]
