from typing import Optional

from pydantic import BaseModel, Field


class SelectedLocation(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    display_name: Optional[str] = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str


class LocationCandidate(BaseModel):
    id: str
    provider: str
    provider_id: int
    name: str
    display_name: str
    latitude: float
    longitude: float
    timezone: str
    country: Optional[str] = None
    country_code: Optional[str] = None
    admin1: Optional[str] = None
    admin2: Optional[str] = None
    admin3: Optional[str] = None
    admin4: Optional[str] = None
    elevation: Optional[float] = None
    population: Optional[int] = None


class LocationSearchResponse(BaseModel):
    query: str
    count: int = Field(ge=1)
    results: list[LocationCandidate]


class ForecastLocationRequest(BaseModel):
    location: SelectedLocation
    days: int = Field(default=7, ge=1, le=14)


class AggregatedForecastLocationRequest(BaseModel):
    location: SelectedLocation
    days: int = Field(default=7, ge=1, le=10)
