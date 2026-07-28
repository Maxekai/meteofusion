from typing import Any

from app.models.weather import (
    ForecastPoint,
    ProviderDailyForecastPoint,
    ProviderForecast,
)
from app.providers.meteosource import fetch_meteosource


SNOW_PRECIPITATION_TYPES = {
    "snow",
    "rain_snow",
    "ice pellets",
    "frozen rain",
}
METERS_PER_SECOND_TO_KMH = 3.6


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


def _precipitation_values(data: dict[str, Any]) -> tuple[float | None, float | None]:
    total = _to_float(_nested_value(data, "precipitation", "total"))
    precipitation_type = _nested_value(data, "precipitation", "type")
    normalized_type = (
        str(precipitation_type).strip().lower()
        if precipitation_type is not None
        else ""
    )

    if total is None:
        return None, None

    # Frozen precipitation keeps the same numeric amount as total.
    snow = total if normalized_type in SNOW_PRECIPITATION_TYPES else 0.0
    return total, snow


def _precipitation_probability(
    data: dict[str, Any],
) -> float | None:
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
