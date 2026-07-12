from typing import Any

from app.models.weather import ForecastPoint, ProviderForecast
from app.providers.weather_api import fetch_weather_api


def _to_float(value: Any) -> float | None:
    if value is None:
        return None

    return float(value)


def calculate_total_precipitation_chance(rain: Any, snow: Any) -> float | None:
    rain_value = _to_float(rain)
    snow_value = _to_float(snow)

    if rain_value is None or snow_value is None:
        return None

    return min(rain_value + snow_value, 100.0)


def normalize_weather_api(data: dict[str, Any]) -> ProviderForecast:
    location = data.get("location", {})
    daily_forecast = data.get("forecast", {}).get("forecastday", [])
    hourly = [hour for day in daily_forecast for hour in day.get("hour", [])]

    points: list[ForecastPoint] = []

    for hour in hourly:
        points.append(
            ForecastPoint(
                datetime=hour.get("time"),
                temperature_c=hour.get("temp_c"),
                humidity_percent=hour.get("humidity"),
                precipitation_probability=calculate_total_precipitation_chance(
                    hour.get("chance_of_rain"),
                    hour.get("chance_of_snow"),
                ),
                cloud_cover=hour.get("cloud"),
                wind_speed_kmh=hour.get("wind_kph"),
                dew_point_c=hour.get("dewpoint_c"),
                precipitation_total=hour.get("precip_mm"),
                precipitation_snow=hour.get("snow_cm"),
                apparent_temperature_c=hour.get("feelslike_c"),
            )
        )

    return ProviderForecast(
        provider="weather_api",
        latitude=location["lat"],
        longitude=location["lon"],
        timezone=location["tz_id"],
        forecast=points,
    )

async def obtain_weather_api_forecast(
    latitude: float,
    longitude: float,
    days: int,
) -> ProviderForecast:
    raw_data = await fetch_weather_api(
        latitude=latitude,
        longitude=longitude,
        days=days,
    )

    return normalize_weather_api(raw_data)
