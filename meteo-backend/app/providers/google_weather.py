from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.exceptions import WeatherProviderError


GOOGLE_WEATHER_URL = "https://weather.googleapis.com/v1/forecast/hours:lookup"
GOOGLE_WEATHER_DAILY_URL = "https://weather.googleapis.com/v1/forecast/days:lookup"
GOOGLE_WEATHER_MAX_DAYS = 10
GOOGLE_WEATHER_MAX_HOURS = 240
GOOGLE_WEATHER_PAGE_SIZE = 24


async def fetch_google_weather(
    latitude: float,
    longitude: float,
    days: int,
) -> dict[str, Any]:
    settings = get_settings()

    if not settings.google_weather_api_key:
        raise WeatherProviderError(
            "Google Weather API no esta configurada. Define GOOGLE_WEATHER_API_KEY."
        )

    if days > GOOGLE_WEATHER_MAX_DAYS:
        raise WeatherProviderError(
            "Google Weather API solo admite hasta 10 dias de prediccion."
        )

    total_hours = min(days * 24, GOOGLE_WEATHER_MAX_HOURS)
    params = {
        "key": settings.google_weather_api_key,
        "location.latitude": latitude,
        "location.longitude": longitude,
        "hours": total_hours,
        "pageSize": GOOGLE_WEATHER_PAGE_SIZE,
        "unitsSystem": "METRIC",
    }
    timeout = httpx.Timeout(settings.http_timeout_seconds)
    aggregated_response: dict[str, Any] = {
        "forecastHours": [],
        "forecastDays": [],
        "timeZone": None,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            next_page_token: str | None = None

            while True:
                request_params = dict(params)
                if next_page_token:
                    request_params["pageToken"] = next_page_token

                response = await client.get(GOOGLE_WEATHER_URL, params=request_params)
                response.raise_for_status()
                payload = response.json()

                if aggregated_response["timeZone"] is None:
                    aggregated_response["timeZone"] = payload.get("timeZone")

                aggregated_response["forecastHours"].extend(
                    payload.get("forecastHours", [])
                )

                next_page_token = payload.get("nextPageToken")
                if not next_page_token:
                    break

                if len(aggregated_response["forecastHours"]) >= total_hours:
                    break

            daily_response = await client.get(
                GOOGLE_WEATHER_DAILY_URL,
                params={
                    "key": settings.google_weather_api_key,
                    "location.latitude": latitude,
                    "location.longitude": longitude,
                    "days": days,
                    "pageSize": days,
                    "unitsSystem": "METRIC",
                },
            )
            daily_response.raise_for_status()
            daily_payload = daily_response.json()
            aggregated_response["forecastDays"] = daily_payload.get(
                "forecastDays",
                [],
            )
            if aggregated_response["timeZone"] is None:
                aggregated_response["timeZone"] = daily_payload.get("timeZone")

        aggregated_response["forecastHours"] = aggregated_response["forecastHours"][
            :total_hours
        ]
        return aggregated_response

    except httpx.TimeoutException as exc:
        raise WeatherProviderError(
            "Google Weather API ha superado el tiempo maximo de espera."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise WeatherProviderError(
            f"Google Weather API respondio con estado {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise WeatherProviderError(
            "No se ha podido conectar con Google Weather API."
        ) from exc

    except ValueError as exc:
        raise WeatherProviderError(
            "Google Weather API devolvio una respuesta JSON invalida."
        ) from exc
