from enum import Enum
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.models.weather import AggregatedForecast, ProviderForecast
from app.providers.exceptions import WeatherProviderError
from app.services.consensus_weather_service import obtain_aggregated_weather_forecast
from app.services.google_weather_service import obtain_google_weather_forecast
from app.services.open_meteo_service import obtain_open_meteo_forecast
from app.services.weather_api import obtain_weather_api_forecast


class WeatherProvider(str, Enum):
    GOOGLE_WEATHER = "google_weather"
    OPEN_METEO = "open_meteo"
    WEATHER_API = "weather_api"

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/aggregate/forecast", response_model=AggregatedForecast)
async def get_aggregated_forecast(
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    days: Annotated[int, Query(ge=1, le=10)] = 7,
) -> AggregatedForecast:
    try:
        return await obtain_aggregated_weather_forecast(
            latitude=latitude,
            longitude=longitude,
            days=days,
        )
    except WeatherProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get("/{provider}/forecast", response_model=ProviderForecast)
async def get_forecast(
    provider: Annotated[WeatherProvider, Path()],
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    days: Annotated[int, Query(ge=1, le=14)] = 7,
) -> ProviderForecast:
    try:
        forecast_provider = {
            WeatherProvider.GOOGLE_WEATHER: obtain_google_weather_forecast,
            WeatherProvider.OPEN_METEO: obtain_open_meteo_forecast,
            WeatherProvider.WEATHER_API: obtain_weather_api_forecast,
        }[provider]

        return await forecast_provider(
            latitude=latitude,
            longitude=longitude,
            days=days,
        )
    except WeatherProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
