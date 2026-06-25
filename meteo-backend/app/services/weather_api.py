from typing import Any

from app.models.weather import ForecastPoint, ProviderForecast
from app.providers.weather_api import fetch_weather_api


def calculate_total_precipitation_chance(rain, snow):
    if rain == None or snow == None:
        return None
    
    return min(rain + snow, 100)  # In case it exceeds 100 due to rounding errors, we only take 100.


def normalize_weather_api(data: dict[str, Any]) -> ProviderForecast:
    daily_forecast = data.get("forecast", {}).get("forecastday", [])
    hourly = [hour for day in daily_forecast for hour in day["hour"]]
    
    points: list[ForecastPoint] = []

    for hour in hourly:
        points.append(
            ForecastPoint(
                datetime=hour.get("time"),
                temperature_c=hour.get("temp_c"),
                humidity_percent=hour.get("humidity"),
                precipitation_probability=calculate_total_precipitation_chance(hour.get("chance_of_rain"), hour.get("chance_of_snow")),
                cloud_cover = hour.get("cloud"),
                wind_speed_kmh=hour.get("wind_kph"),
                dew_point_c=hour.get("dewpoint_c"),
                precipitation_total=hour.get("precip_mm"),
                precipitation_snow=hour.get("snow_cm"),
                apparent_temperature_c=hour.get("feelslike_c")
            )
        )

    return ProviderForecast(
        provider="open_meteo",
        latitude=data["latitude"],
        longitude=data["longitude"],
        timezone=data["timezone"],
        forecast=points,
    )
    

    

async def obtain_weather_forecast(
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