from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.exceptions import WeatherProviderError


METEOSOURCE_URL = "https://www.meteosource.com/api/v1/free/point"


async def fetch_meteosource(
    latitude: float,
    longitude: float,
    days: int,
) -> dict[str, Any]:
    settings = get_settings()

    if not settings.meteosource_api_key:
        raise WeatherProviderError(
            "Meteosource no esta configurado. Define METEOSOURCE_API_KEY."
        )

    params = {
        "lat": latitude,
        "lon": longitude,
        "sections": "hourly,daily",
        "timezone": "auto",
        "language": "en",
        "units": "metric",
    }
    headers = {
        "X-API-Key": settings.meteosource_api_key,
    }
    timeout = httpx.Timeout(settings.http_timeout_seconds)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(
                METEOSOURCE_URL,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException as exc:
        raise WeatherProviderError(
            "Meteosource ha superado el tiempo maximo de espera."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise WeatherProviderError(
            f"Meteosource respondio con estado {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise WeatherProviderError(
            "No se ha podido conectar con Meteosource."
        ) from exc

    except ValueError as exc:
        raise WeatherProviderError(
            "Meteosource devolvio una respuesta JSON invalida."
        ) from exc
