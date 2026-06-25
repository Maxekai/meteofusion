from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.exceptions import WeatherProviderError


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_open_meteo(
    latitude: float,
    longitude: float,
    days: int,
) -> dict[str, Any]:
    settings = get_settings()
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "forecast_days": days,
        "timezone": "auto",
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation_probability",
            "cloud_cover"
            "wind_speed_10m",
            "dew_point_2m",
            "apparent_temperature",
            "precipitation",
            "snowfall",
        ],
    }

    timeout = httpx.Timeout(settings.http_timeout_seconds)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException as exc:
        raise WeatherProviderError(
            "Open-Meteo ha superado el tiempo maximo de espera."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise WeatherProviderError(
            f"Open-Meteo respondio con estado {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise WeatherProviderError(
            "No se ha podido conectar con Open-Meteo."
        ) from exc

    except ValueError as exc:
        raise WeatherProviderError(
            "Open-Meteo devolvio una respuesta JSON invalida."
        ) from exc
