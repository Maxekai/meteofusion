from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.models.weather import ProviderForecast
from app.providers.open_meteo import WeatherProviderError
from app.services.weather_service import obtain_weather_forecast

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/forecast", response_model=ProviderForecast)
async def get_forecast(
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    days: Annotated[int, Query(ge=1, le=14)] = 3,
) -> ProviderForecast:
    try:
        return await obtain_weather_forecast(
            latitude=latitude,
            longitude=longitude,
            days=days,
        )
    except WeatherProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
