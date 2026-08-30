from typing import Any

from app.models.weather import (
    ForecastPoint,
    ProviderDailyForecastPoint,
    ProviderForecast,
)
from app.providers.meteosource import fetch_meteosource
from app.services.weather_units import snowfall_cm_from_swe_mm


METERS_PER_SECOND_TO_KMH = 3.6
SUPPORTED_PRECIPITATION_TYPES = {"none", "rain", "snow"}


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


def _precipitation_type(data: dict[str, Any]) -> str | None:
    value = _nested_value(data, "precipitation", "type")
    if value is None:
        return None

    return str(value).strip().lower()


def _has_unsupported_precipitation_type(data: dict[str, Any]) -> bool:
    precipitation_type = _precipitation_type(data)
    return (
        precipitation_type is not None
        and precipitation_type not in SUPPORTED_PRECIPITATION_TYPES
    )


def _precipitation_values(data: dict[str, Any]) -> tuple[float | None, float | None]:
    if _has_unsupported_precipitation_type(data):
        return None, None

    total = _to_float(_nested_value(data, "precipitation", "total"))
    precipitation_type = _precipitation_type(data)

    if total is None:
        return None, None

    if precipitation_type == "snow":
        snow = snowfall_cm_from_swe_mm(total)
    else:
        snow = 0.0

    return total, snow


def _precipitation_probability(
    data: dict[str, Any],
) -> float | None:
    if _has_unsupported_precipitation_type(data):
        return None

    probability = _to_float(_nested_value(data, "probability", "precipitation"))
    if probability is None:
        return None

    return min(max(probability, 0.0), 100.0)


def _wind_speed_kmh(data: dict[str, Any]) -> float | None:
    speed_meters_per_second = _to_float(_nested_value(data, "wind", "speed"))
    if speed_meters_per_second is None:
        return None

    return speed_meters_per_second * METERS_PER_SECOND_TO_KMH


def normalize_meteosource(
    data: dict[str, Any],
    latitude: float,
    longitude: float,
    days: int,
) -> ProviderForecast:
    hourly_data = data.get("hourly", {}).get("data", [])
    daily_data = data.get("daily", {}).get("data", [])
    maximum_hours = days * 24

    points: list[ForecastPoint] = []

    for hour in hourly_data[:maximum_hours]:
        timestamp = hour.get("date")
        if not timestamp:
            continue

        precipitation_total, precipitation_snow = _precipitation_values(hour)
        points.append(
            ForecastPoint(
                datetime=timestamp,
                temperature_c=hour.get("temperature"),
                humidity_percent=hour.get("humidity"),
                precipitation_probability=_precipitation_probability(
                    hour,
                ),
                precipitation_total=precipitation_total,
                precipitation_snow=precipitation_snow,
                cloud_cover=_nested_value(hour, "cloud_cover", "total"),
                wind_speed_kmh=_wind_speed_kmh(hour),
                apparent_temperature_c=hour.get("feels_like"),
            )
        )

    daily_points: list[ProviderDailyForecastPoint] = []

    for day in daily_data[:days]:
        forecast_date = day.get("day")
        all_day = day.get("all_day")
        if not forecast_date or not isinstance(all_day, dict):
            continue

        precipitation_total, precipitation_snow = _precipitation_values(all_day)
        daily_points.append(
            ProviderDailyForecastPoint(
                date=forecast_date,
                temperature_min_c=all_day.get("temperature_min"),
                temperature_max_c=all_day.get("temperature_max"),
                precipitation_total=precipitation_total,
                precipitation_snow=precipitation_snow,
                cloud_cover=_nested_value(all_day, "cloud_cover", "total"),
            )
        )

    return ProviderForecast(
        provider="meteosource",
        latitude=latitude,
        longitude=longitude,
        timezone=data.get("timezone") or "UTC",
        forecast=points,
        daily_forecast=daily_points,
    )


async def obtain_meteosource_forecast(
    latitude: float,
    longitude: float,
    days: int,
) -> ProviderForecast:
    raw_data = await fetch_meteosource(
        latitude=latitude,
        longitude=longitude,
        days=days,
    )

    return normalize_meteosource(
        data=raw_data,
        latitude=latitude,
        longitude=longitude,
        days=days,
    )
