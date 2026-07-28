import asyncio
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.exceptions import WeatherProviderError


XWEATHER_FORECASTS_URL = "https://data.api.xweather.com/forecasts"
XWEATHER_MAX_FORECAST_DAYS = 15
HOURS_PER_DAY = 24
XWEATHER_HOURLY_FIELDS = ",".join(
    [
        "periods.dateTimeISO",
        "periods.tempC",
        "periods.feelslikeC",
        "periods.humidity",
        "periods.pop",
        "periods.precipMM",
        "periods.snowCM",
        "periods.sky",
        "periods.windSpeedKPH",
        "profile.tz",
    ]
)
XWEATHER_DAILY_FIELDS = ",".join(
    [
        "periods.dateTimeISO",
        "periods.minTempC",
        "periods.maxTempC",
        "periods.precipMM",
        "periods.snowCM",
        "periods.sky",
        "profile.tz",
    ]
)


def _error_description(data: dict[str, Any]) -> str | None:
    error = data.get("error")
    if not isinstance(error, dict):
        return None

    description = error.get("description")
    return str(description) if description else None


def _validate_payload(data: Any, interval: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise WeatherProviderError(
            f"Xweather devolvio un pronostico {interval} invalido."
        )

    if data.get("success") is False:
        description = _error_description(data)
        detail = f": {description}" if description else ""
        raise WeatherProviderError(
            f"Xweather rechazo el pronostico {interval}{detail}."
        )

    return data


async def fetch_xweather(
    latitude: float,
    longitude: float,
    days: int,
) -> dict[str, dict[str, Any]]:
    settings = get_settings()

    if not settings.xweather_client_id or not settings.xweather_client_secret:
        raise WeatherProviderError(
            "Xweather no esta configurado. Define XWEATHER_CLIENT_ID y "
            "XWEATHER_CLIENT_SECRET."
        )

    requested_days = min(max(days, 1), XWEATHER_MAX_FORECAST_DAYS)
    configured_hourly_limit = min(
        max(settings.xweather_hourly_period_limit, 1),
        XWEATHER_MAX_FORECAST_DAYS * HOURS_PER_DAY,
    )
    hourly_limit = min(requested_days * HOURS_PER_DAY, configured_hourly_limit)
    location = f"{latitude},{longitude}"
    url = f"{XWEATHER_FORECASTS_URL}/{location}"
    common_params = {
        "client_id": settings.xweather_client_id,
        "client_secret": settings.xweather_client_secret,
    }
    hourly_params = {
        **common_params,
        "filter": "1hr",
        "limit": hourly_limit,
        "fields": XWEATHER_HOURLY_FIELDS,
    }
    daily_params = {
        **common_params,
        "filter": "day",
        "limit": requested_days,
        "fields": XWEATHER_DAILY_FIELDS,
    }
    timeout = httpx.Timeout(settings.http_timeout_seconds)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            hourly_response, daily_response = await asyncio.gather(
                client.get(url, params=hourly_params),
                client.get(url, params=daily_params),
            )
            hourly_response.raise_for_status()
            daily_response.raise_for_status()
            hourly_data = hourly_response.json()
            daily_data = daily_response.json()

    except httpx.TimeoutException as exc:
        raise WeatherProviderError(
            "Xweather ha superado el tiempo maximo de espera."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise WeatherProviderError(
            f"Xweather respondio con estado {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise WeatherProviderError(
            "No se ha podido conectar con Xweather."
        ) from exc

    except ValueError as exc:
        raise WeatherProviderError(
            "Xweather devolvio una respuesta JSON invalida."
        ) from exc

    return {
        "hourly": _validate_payload(hourly_data, "horario"),
        "daily": _validate_payload(daily_data, "diario"),
    }
