from typing import Any

from app.models.weather import ForecastPoint, ProviderForecast
from app.providers.open_meteo import fetch_open_meteo


def normalize_open_meteo(data: dict[str, Any]) -> ProviderForecast:
    hourly = data.get("hourly", {})

    times = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    humidity = hourly.get("relative_humidity_2m", [])
    precipitation = hourly.get("precipitation_probability", [])
    wind = hourly.get("wind_speed_10m", [])
    dew_point = hourly.get("dew_point_2m", [])
    precipitation_amounts = hourly.get("precipitation", [])
    snowfall = hourly.get("snowfall", [])
    apparent_temperature = hourly.get("apparent_temperature", [])

    points: list[ForecastPoint] = []

    for index, timestamp in enumerate(times):
        points.append(
            ForecastPoint(
                datetime=timestamp,
                temperature_c=temperatures[index]
                if index < len(temperatures)
                else None,
                humidity_percent=humidity[index]
                if index < len(humidity)
                else None,
                precipitation_probability=precipitation[index]
                if index < len(precipitation)
                else None,
                wind_speed_kmh=wind[index]
                if index < len(wind)
                else None,
                dew_point_c=dew_point[index]
                if index < len(dew_point)
                else None,
                precipitation_total=precipitation_amounts[index]
                if index < len(precipitation_amounts)
                else None,
                precipitation_snow=snowfall[index]
                if index < len(snowfall)
                else None,
                apparent_temperature_c=apparent_temperature[index]
                if index < len(apparent_temperature)
                else None,
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
    raw_data = await fetch_open_meteo(
        latitude=latitude,
        longitude=longitude,
        days=days,
    )

    return normalize_open_meteo(raw_data)
