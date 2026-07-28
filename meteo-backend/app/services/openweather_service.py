from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.models.weather import ForecastPoint, ProviderForecast
from app.providers.openweather import fetch_openweather


METERS_PER_SECOND_TO_KMH = 3.6
MILLIMETERS_PER_CENTIMETER = 10.0
OPENWEATHER_MAX_CALENDAR_DAYS = 5


def _to_float(value: Any) -> float | None:
    if value is None:
        return None

    return float(value)


def _nested_value(data: Any, *keys: str) -> Any:
    value = data

    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
        if value is None:
            return None

    return value


def _format_timezone_offset(offset_seconds: int) -> str:
    sign = "+" if offset_seconds >= 0 else "-"
    absolute_offset = abs(offset_seconds)
    hours, remainder = divmod(absolute_offset, 3600)
    minutes = remainder // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def _precipitation_values(data: dict[str, Any]) -> tuple[float, float]:
    rain_mm = _to_float(_nested_value(data, "rain", "3h")) or 0.0
    snow_mm = _to_float(_nested_value(data, "snow", "3h")) or 0.0

    return rain_mm + snow_mm, snow_mm / MILLIMETERS_PER_CENTIMETER


def _precipitation_probability(
    data: dict[str, Any],
    precipitation_total: float,
) -> float:
    probability = _to_float(data.get("pop"))
    if probability is None:
        return 100.0 if precipitation_total > 0.0 else 0.0

    return min(max(probability * 100.0, 0.0), 100.0)


def normalize_openweather(
    data: dict[str, Any],
    latitude: float,
    longitude: float,
    days: int,
) -> ProviderForecast:
    city = data.get("city", {})
    offset_seconds = int(city.get("timezone") or 0)
    local_timezone = timezone(timedelta(seconds=offset_seconds))
    timezone_name = _format_timezone_offset(offset_seconds)
    dated_points: list[tuple[date, ForecastPoint]] = []

    for item in data.get("list", []):
        timestamp = item.get("dt")
        if timestamp is None:
            continue

        forecast_datetime = datetime.fromtimestamp(
            int(timestamp),
            tz=timezone.utc,
        )
        precipitation_total, precipitation_snow = _precipitation_values(item)
        wind_speed = _to_float(_nested_value(item, "wind", "speed"))
        dated_points.append(
            (
                forecast_datetime.astimezone(local_timezone).date(),
                ForecastPoint(
                    datetime=forecast_datetime,
                    temperature_c=_nested_value(item, "main", "temp"),
                    humidity_percent=_nested_value(item, "main", "humidity"),
                    precipitation_probability=_precipitation_probability(
                        item,
                        precipitation_total,
                    ),
                    precipitation_total=precipitation_total,
                    precipitation_snow=precipitation_snow,
                    cloud_cover=_nested_value(item, "clouds", "all"),
                    wind_speed_kmh=(
                        wind_speed * METERS_PER_SECOND_TO_KMH
                        if wind_speed is not None
                        else None
                    ),
                    apparent_temperature_c=_nested_value(
                        item,
                        "main",
                        "feels_like",
                    ),
                ),
            )
        )

    available_dates = list(dict.fromkeys(point_date for point_date, _ in dated_points))
    maximum_dates = min(days, OPENWEATHER_MAX_CALENDAR_DAYS)
    selected_dates = set(available_dates[:maximum_dates])
    points = [
        point
        for point_date, point in dated_points
        if point_date in selected_dates
    ]

    return ProviderForecast(
        provider="openweather",
        latitude=latitude,
        longitude=longitude,
        timezone=timezone_name,
        forecast=points,
    )


async def obtain_openweather_forecast(
    latitude: float,
    longitude: float,
    days: int,
) -> ProviderForecast:
    raw_data = await fetch_openweather(
        latitude=latitude,
        longitude=longitude,
        days=days,
    )

    return normalize_openweather(
        data=raw_data,
        latitude=latitude,
        longitude=longitude,
        days=days,
    )
