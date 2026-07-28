from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.exceptions import WeatherProviderError


OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


async def fetch_openweather(
    latitude: float,
    longitude: float,
    days: int,
) -> dict[str, Any]:
    settings = get_settings()

    if not settings.openweather_api_key:
        raise WeatherProviderError(
            "OpenWeather no esta configurado. Define OPENWEATHER_API_KEY."
        )

    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": settings.openweather_api_key,
        "units": "metric",
        "lang": "es",
    }
    timeout = httpx.Timeout(settings.http_timeout_seconds)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                OPENWEATHER_FORECAST_URL,
                params=params,
            )
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException as exc:
        raise WeatherProviderError(
            "OpenWeather ha superado el tiempo maximo de espera."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise WeatherProviderError(
            f"OpenWeather respondio con estado {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise WeatherProviderError(
            "No se ha podido conectar con OpenWeather."
        ) from exc

    except ValueError as exc:
        raise WeatherProviderError(
            "OpenWeather devolvio una respuesta JSON invalida."
        ) from exc
