from typing import Any

from app.models.weather import ForecastPoint, ProviderForecast
from app.providers.google_weather import fetch_google_weather


def _get_nested(data: dict[str, Any], *keys: str) -> Any:
    value: Any = data

    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
        if value is None:
            return None

    return value


def _extract_timezone(data: dict[str, Any]) -> str | None:
    timezone = data.get("timeZone")

    if isinstance(timezone, str):
        return timezone

    if isinstance(timezone, dict):
        timezone_id = timezone.get("id")
        if timezone_id:
            return str(timezone_id)

        utc_offset = timezone.get("utcOffset")
        if utc_offset:
            return str(utc_offset)

    return None


def normalize_google_weather(
    data: dict[str, Any],
    latitude: float,
    longitude: float,
) -> ProviderForecast:
    forecast_hours = data.get("forecastHours", [])
    timezone = _extract_timezone(data)

    points: list[ForecastPoint] = []

    for hour in forecast_hours:
        points.append(
            ForecastPoint(
                datetime=_get_nested(hour, "interval", "startTime"),
                temperature_c=_get_nested(hour, "temperature", "degrees"),
                humidity_percent=hour.get("relativeHumidity"),
                precipitation_probability=_get_nested(
                    hour,
                    "precipitation",
                    "probability",
                    "percent",
                ),
                precipitation_total=_get_nested(
                    hour,
                    "precipitation",
                    "qpf",
                    "quantity",
                ),
                precipitation_snow=_get_nested(
                    hour,
                    "precipitation",
                    "snowQpf",
                    "quantity",
                ),
                cloud_cover=hour.get("cloudCover"),
                wind_speed_kmh=_get_nested(hour, "wind", "speed", "value"),
                dew_point_c=_get_nested(hour, "dewPoint", "degrees"),
                apparent_temperature_c=_get_nested(
                    hour,
                    "feelsLikeTemperature",
                    "degrees",
                ),
            )
        )

    return ProviderForecast(
        provider="google_weather",
        latitude=latitude,
        longitude=longitude,
        timezone=timezone or "UTC",
        forecast=points,
    )


async def obtain_google_weather_forecast(
    latitude: float,
    longitude: float,
    days: int,
) -> ProviderForecast:
    raw_data = await fetch_google_weather(
        latitude=latitude,
        longitude=longitude,
        days=days,
    )

    return normalize_google_weather(
        data=raw_data,
        latitude=latitude,
        longitude=longitude,
    )
