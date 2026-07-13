from typing import Any, Optional

import httpx

from app.core.config import get_settings
from app.providers.exceptions import LocationProviderError


OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"


async def fetch_open_meteo_locations(
    query: str,
    count: int = 10,
    language: str = "es",
    country_code: Optional[str] = None,
) -> dict[str, Any]:
    settings = get_settings()
    params: dict[str, Any] = {
        "name": query,
        "count": count,
        "language": language,
        "format": "json",
    }
    if country_code:
        params["countryCode"] = country_code

    timeout = httpx.Timeout(settings.http_timeout_seconds)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(OPEN_METEO_GEOCODING_URL, params=params)
            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException as exc:
        raise LocationProviderError(
            "Open-Meteo Geocoding ha superado el tiempo maximo de espera."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise LocationProviderError(
            f"Open-Meteo Geocoding respondio con estado {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise LocationProviderError(
            "No se ha podido conectar con Open-Meteo Geocoding."
        ) from exc

    except ValueError as exc:
        raise LocationProviderError(
            "Open-Meteo Geocoding devolvio una respuesta JSON invalida."
        ) from exc
