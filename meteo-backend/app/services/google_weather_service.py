from datetime import date
from typing import Any

from app.models.weather import (
    ForecastPoint,
    ProviderDailyForecastPoint,
    ProviderForecast,
)
from app.providers.google_weather import fetch_google_weather
from app.services.weather_units import snowfall_cm_from_swe_mm


def get_nested(data: dict[str, Any], *keys: str) -> Any:
    value: Any = data

    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
        if value is None:
            return None

    return value


def extract_timezone(data: dict[str, Any]) -> str | None:
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


def _display_date(value: Any) -> date | None:
    if not isinstance(value, dict):
        return None

    try:
        return date(
            year=int(value["year"]),
            month=int(value["month"]),
            day=int(value["day"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _sum_available(*values: Any) -> float | None:
    numeric_values = [float(value) for value in values if value is not None]
    return sum(numeric_values) if numeric_values else None


def _mean_available(*values: Any) -> float | None:
    numeric_values = [float(value) for value in values if value is not None]
    return sum(numeric_values) / len(numeric_values) if numeric_values else None


def _snow_qpf_to_cm(value: Any) -> float | None:
    quantity = get_nested(value, "quantity")
    if quantity is None:
        return None

    return snowfall_cm_from_swe_mm(float(quantity))


def normalize_google_weather(
    data: dict[str, Any],
    latitude: float,
    longitude: float,
) -> ProviderForecast:
    forecast_hours = data.get("forecastHours", [])
    forecast_days = data.get("forecastDays", [])
    timezone = extract_timezone(data)

    points: list[ForecastPoint] = []

    for hour in forecast_hours:
        points.append(
            ForecastPoint(
                datetime=get_nested(hour, "interval", "startTime"),
                temperature_c=get_nested(hour, "temperature", "degrees"),
                humidity_percent=hour.get("relativeHumidity"),
                precipitation_probability=get_nested(
                    hour,
                    "precipitation",
                    "probability",
                    "percent",
                ),
                precipitation_total=get_nested(
                    hour,
                    "precipitation",
                    "qpf",
                    "quantity",
                ),
                precipitation_snow=_snow_qpf_to_cm(
                    get_nested(hour, "precipitation", "snowQpf"),
                ),
                cloud_cover=hour.get("cloudCover"),
                wind_speed_kmh=get_nested(hour, "wind", "speed", "value"),
                apparent_temperature_c=get_nested(
                    hour,
                    "feelsLikeTemperature",
                    "degrees",
                ),
            )
        )

    daily_points: list[ProviderDailyForecastPoint] = []

    for forecast_day in forecast_days:
        forecast_date = _display_date(forecast_day.get("displayDate"))
        if forecast_date is None:
            continue

        daytime = forecast_day.get("daytimeForecast", {})
        nighttime = forecast_day.get("nighttimeForecast", {})
        daily_points.append(
            ProviderDailyForecastPoint(
                date=forecast_date,
                temperature_min_c=get_nested(
                    forecast_day,
                    "minTemperature",
                    "degrees",
                ),
                temperature_max_c=get_nested(
                    forecast_day,
                    "maxTemperature",
                    "degrees",
                ),
                precipitation_total=_sum_available(
                    get_nested(daytime, "precipitation", "qpf", "quantity"),
                    get_nested(nighttime, "precipitation", "qpf", "quantity"),
                ),
                precipitation_snow=_sum_available(
                    _snow_qpf_to_cm(
                        get_nested(daytime, "precipitation", "snowQpf"),
                    ),
                    _snow_qpf_to_cm(
                        get_nested(nighttime, "precipitation", "snowQpf"),
                    ),
                ),
                cloud_cover=_mean_available(
                    daytime.get("cloudCover"),
                    nighttime.get("cloudCover"),
                ),
            )
        )

    return ProviderForecast(
        provider="google_weather",
        latitude=latitude,
        longitude=longitude,
        timezone=timezone or "UTC",
        forecast=points,
        daily_forecast=daily_points,
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
