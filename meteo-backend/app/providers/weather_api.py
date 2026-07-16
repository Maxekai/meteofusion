from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.exceptions import WeatherProviderError


WEATHER_API_URL = "https://api.weatherapi.com/v1/forecast.json"


async def fetch_weather_api(
    latitude: float,
    longitude: float,
    days: int,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.weather_api_key:
        raise WeatherProviderError(
            "WeatherAPI no esta configurado. Define WEATHER_API_KEY."
        )

    params = {
        "key": settings.weather_api_key,
        "q": f"{latitude},{longitude}",
        "days": days,
        "aqi": "no",
        "alerts": "no",
    }

    timeout = httpx.Timeout(settings.http_timeout_seconds)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(WEATHER_API_URL, params=params)
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException as exc:
        raise WeatherProviderError(
            "Weather-API ha superado el tiempo maximo de espera."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise WeatherProviderError(
            f"Weather-API respondio con estado {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise WeatherProviderError(
            "No se ha podido conectar con Weather-API."
        ) from exc

    except ValueError as exc:
        raise WeatherProviderError(
            "Weather-API devolvio una respuesta JSON invalida."
        ) from exc
