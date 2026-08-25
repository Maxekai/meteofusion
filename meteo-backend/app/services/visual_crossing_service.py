from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.models.weather import (
    ForecastPoint,
    ProviderDailyForecastPoint,
    ProviderForecast,
)
from app.providers.visual_crossing import fetch_visual_crossing


def _to_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _bounded_value(
    value: Any,
    minimum: float = 0.0,
    maximum: float | None = None,
) -> float | None:
    numeric_value = _to_float(value)
    if numeric_value is None:
        return None

    numeric_value = max(numeric_value, minimum)
    if maximum is not None:
        numeric_value = min(numeric_value, maximum)

    return numeric_value


def _epoch_datetime(value: Any) -> datetime | None:
    timestamp = _to_float(value)
    if timestamp is None:
        return None

    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (OSError, OverflowError, ValueError):
        return None


def _day_date(day: dict[str, Any], timezone_name: str) -> date | None:
    date_value = day.get("datetime")
    if date_value:
        try:
            return date.fromisoformat(str(date_value).split("T", 1)[0])
        except ValueError:
            pass

    forecast_datetime = _epoch_datetime(day.get("datetimeEpoch"))
    if forecast_datetime is None:
        return None

    try:
        return forecast_datetime.astimezone(ZoneInfo(timezone_name)).date()
    except ZoneInfoNotFoundError:
        return forecast_datetime.date()


def _hour_datetime(
    hour: dict[str, Any],
    forecast_date: date | None,
) -> datetime | None:
    forecast_datetime = _epoch_datetime(hour.get("datetimeEpoch"))
    if forecast_datetime is not None:
        return forecast_datetime

    datetime_value = hour.get("datetime")
    if not datetime_value:
        return None

    raw_datetime = str(datetime_value).replace("Z", "+00:00")
    if "T" not in raw_datetime:
        if forecast_date is None:
            return None
        raw_datetime = f"{forecast_date.isoformat()}T{raw_datetime}"

    try:
        return datetime.fromisoformat(raw_datetime)
    except ValueError:
        return None


def normalize_visual_crossing(
    data: dict[str, Any],
    latitude: float,
    longitude: float,
    days: int,
) -> ProviderForecast:
    timezone_name = str(data.get("timezone") or "UTC")
    daily_data = data.get("days", [])
    if not isinstance(daily_data, list):
        daily_data = []

    points: list[ForecastPoint] = []
    daily_points: list[ProviderDailyForecastPoint] = []

    for day in daily_data[: max(days, 1)]:
        if not isinstance(day, dict):
            continue

        forecast_date = _day_date(day, timezone_name)
        hours = day.get("hours", [])
        if isinstance(hours, list):
            for hour in hours:
                if not isinstance(hour, dict):
                    continue

                forecast_datetime = _hour_datetime(hour, forecast_date)
                if forecast_datetime is None:
                    continue

                points.append(
                    ForecastPoint(
                        datetime=forecast_datetime,
                        temperature_c=_to_float(hour.get("temp")),
                        humidity_percent=_bounded_value(
                            hour.get("humidity"),
                            maximum=100.0,
                        ),
                        precipitation_probability=_bounded_value(
                            hour.get("precipprob"),
                            maximum=100.0,
                        ),
                        precipitation_total=_bounded_value(hour.get("precip")),
                        precipitation_snow=_bounded_value(hour.get("snow")),
                        cloud_cover=_bounded_value(
                            hour.get("cloudcover"),
                            maximum=100.0,
                        ),
                        wind_speed_kmh=_bounded_value(hour.get("windspeed")),
                        apparent_temperature_c=_to_float(hour.get("feelslike")),
                    )
                )

        if forecast_date is None:
            continue

        daily_points.append(
            ProviderDailyForecastPoint(
                date=forecast_date,
                temperature_min_c=_to_float(day.get("tempmin")),
                temperature_max_c=_to_float(day.get("tempmax")),
                precipitation_total=_bounded_value(day.get("precip")),
                precipitation_snow=_bounded_value(day.get("snow")),
                cloud_cover=_bounded_value(
                    day.get("cloudcover"),
                    maximum=100.0,
                ),
            )
        )

    return ProviderForecast(
        provider="visual_crossing",
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_name,
        forecast=points,
        daily_forecast=daily_points,
    )


async def obtain_visual_crossing_forecast(
    latitude: float,
    longitude: float,
    days: int,
) -> ProviderForecast:
    raw_data = await fetch_visual_crossing(
        latitude=latitude,
        longitude=longitude,
        days=days,
    )

    return normalize_visual_crossing(
        data=raw_data,
        latitude=latitude,
        longitude=longitude,
        days=days,
    )
