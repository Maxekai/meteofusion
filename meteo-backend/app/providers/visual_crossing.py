from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.exceptions import WeatherProviderError


VISUAL_CROSSING_TIMELINE_URL = (
    "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/"
    "timeline"
)
VISUAL_CROSSING_MAX_FORECAST_DAYS = 15
VISUAL_CROSSING_ELEMENTS = ",".join(
    [
        "datetime",
        "datetimeEpoch",
        "timezone",
        "temp",
        "tempmin",
        "tempmax",
        "feelslike",
        "humidity",
        "precip",
        "precipprob",
        "snow",
        "cloudcover",
        "windspeed",
    ]
)


def _validate_payload(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("days"), list):
        raise WeatherProviderError(
            "Visual Crossing devolvio un pronostico invalido."
        )

    return data


async def fetch_visual_crossing(
    latitude: float,
    longitude: float,
    days: int,
) -> dict[str, Any]:
    settings = get_settings()

    if not settings.visual_crossing_api_key:
        raise WeatherProviderError(
            "Visual Crossing no esta configurado. Define "
            "VISUAL_CROSSING_API_KEY."
        )

    requested_days = min(max(days, 1), VISUAL_CROSSING_MAX_FORECAST_DAYS)
    location = f"{latitude},{longitude}"
    period = f"next{requested_days}days"
    url = f"{VISUAL_CROSSING_TIMELINE_URL}/{location}/{period}"
    params = {
        "key": settings.visual_crossing_api_key,
        "unitGroup": "metric",
        "include": "days,hours",
        "elements": VISUAL_CROSSING_ELEMENTS,
        "contentType": "json",
    }
    timeout = httpx.Timeout(settings.http_timeout_seconds)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

    except httpx.TimeoutException as exc:
        raise WeatherProviderError(
            "Visual Crossing ha superado el tiempo maximo de espera."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise WeatherProviderError(
            f"Visual Crossing respondio con estado {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise WeatherProviderError(
            "No se ha podido conectar con Visual Crossing."
        ) from exc

    except ValueError as exc:
        raise WeatherProviderError(
            "Visual Crossing devolvio una respuesta JSON invalida."
        ) from exc

    return _validate_payload(data)
