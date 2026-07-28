from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models.weather import (
    ForecastPoint,
    ProviderDailyForecastPoint,
    ProviderForecast,
)
from app.providers.xweather import fetch_xweather


def _to_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _forecast_response(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    response = data.get("response")
    if isinstance(response, list):
        return response[0] if response and isinstance(response[0], dict) else {}

    return response if isinstance(response, dict) else {}


def _timezone_name(*responses: dict[str, Any]) -> str:
    for response in responses:
        profile = response.get("profile")
        if isinstance(profile, dict) and profile.get("tz"):
            return str(profile["tz"])

    return "UTC"


def _period_datetime(
    period: dict[str, Any],
    timezone_name: str,
) -> datetime | None:
    date_time_value = period.get("dateTimeISO") or period.get("validTime")
    if date_time_value:
        try:
            return datetime.fromisoformat(str(date_time_value).replace("Z", "+00:00"))
        except ValueError:
            pass

    timestamp = _to_float(period.get("timestamp"))
    if timestamp is None:
        return None

    forecast_datetime = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    try:
        return forecast_datetime.astimezone(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError:
        return forecast_datetime


def _precipitation_values(
    period: dict[str, Any],
) -> tuple[float | None, float | None]:
    precipitation_total = _to_float(period.get("precipMM"))
    precipitation_snow = _to_float(period.get("snowCM"))

    if precipitation_total is not None:
        precipitation_total = max(precipitation_total, 0.0)
    if precipitation_snow is not None:
        precipitation_snow = max(precipitation_snow, 0.0)

    return precipitation_total, precipitation_snow


def _precipitation_probability(
    period: dict[str, Any],
) -> float | None:
    probability = _to_float(period.get("pop"))
    if probability is None:
        return None

    return min(max(probability, 0.0), 100.0)


def normalize_xweather(
    data: dict[str, dict[str, Any]],
    latitude: float,
    longitude: float,
    days: int,
) -> ProviderForecast:
    hourly_response = _forecast_response(data.get("hourly"))
    daily_response = _forecast_response(data.get("daily"))
    timezone_name = _timezone_name(hourly_response, daily_response)
    maximum_hours = max(days, 1) * 24
    hourly_periods = hourly_response.get("periods", [])
    daily_periods = daily_response.get("periods", [])
    points: list[ForecastPoint] = []

    if not isinstance(hourly_periods, list):
        hourly_periods = []

    for period in hourly_periods[:maximum_hours]:
        if not isinstance(period, dict):
            continue

        forecast_datetime = _period_datetime(period, timezone_name)
        if forecast_datetime is None:
            continue

        precipitation_total, precipitation_snow = _precipitation_values(period)
        points.append(
            ForecastPoint(
                datetime=forecast_datetime,
                temperature_c=_to_float(period.get("tempC")),
                humidity_percent=_to_float(period.get("humidity")),
                precipitation_probability=_precipitation_probability(
                    period,
                ),
                precipitation_total=precipitation_total,
                precipitation_snow=precipitation_snow,
                cloud_cover=_to_float(period.get("sky")),
                wind_speed_kmh=_to_float(period.get("windSpeedKPH")),
                apparent_temperature_c=_to_float(period.get("feelslikeC")),
            )
        )

    daily_points: list[ProviderDailyForecastPoint] = []

    if not isinstance(daily_periods, list):
        daily_periods = []

    for period in daily_periods[: max(days, 1)]:
        if not isinstance(period, dict):
            continue

        forecast_datetime = _period_datetime(period, timezone_name)
        if forecast_datetime is None:
            continue

        precipitation_total, precipitation_snow = _precipitation_values(period)
        daily_points.append(
            ProviderDailyForecastPoint(
                date=forecast_datetime.date(),
                temperature_min_c=_to_float(period.get("minTempC")),
                temperature_max_c=_to_float(period.get("maxTempC")),
                precipitation_total=precipitation_total,
                precipitation_snow=precipitation_snow,
                cloud_cover=_to_float(period.get("sky")),
            )
        )

    return ProviderForecast(
        provider="xweather",
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_name,
        forecast=points,
        daily_forecast=daily_points,
    )


async def obtain_xweather_forecast(
    latitude: float,
    longitude: float,
    days: int,
) -> ProviderForecast:
    raw_data = await fetch_xweather(
        latitude=latitude,
        longitude=longitude,
        days=days,
    )

    return normalize_xweather(
        data=raw_data,
        latitude=latitude,
        longitude=longitude,
        days=days,
    )
