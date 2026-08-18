from typing import Any

from app.models.weather import (
    ForecastPoint,
    ProviderDailyForecastPoint,
    ProviderForecast,
)
from app.providers.open_meteo import fetch_open_meteo


def normalize_open_meteo(data: dict[str, Any]) -> ProviderForecast:
    hourly = data.get("hourly", {})
    daily = data.get("daily", {})

    times = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    humidity = hourly.get("relative_humidity_2m", [])
    precipitation = hourly.get("precipitation_probability", [])
    clouds = hourly.get("cloud_cover", [])
    wind = hourly.get("wind_speed_10m", [])
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
                cloud_cover=clouds[index]
                if index < len(clouds)
                else None,
                wind_speed_kmh=wind[index]
                if index < len(wind)
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

    daily_times = daily.get("time", [])
    daily_minimums = daily.get("temperature_2m_min", [])
    daily_maximums = daily.get("temperature_2m_max", [])
    daily_precipitation = daily.get("precipitation_sum", [])
    daily_snowfall = daily.get("snowfall_sum", [])
    daily_points: list[ProviderDailyForecastPoint] = []

    for index, forecast_date in enumerate(daily_times):
        day_clouds = [
            float(cloud_cover)
            for timestamp, cloud_cover in zip(times, clouds)
            if str(timestamp).startswith(str(forecast_date))
            and cloud_cover is not None
        ]
        daily_points.append(
            ProviderDailyForecastPoint(
                date=forecast_date,
                temperature_min_c=daily_minimums[index]
                if index < len(daily_minimums)
                else None,
                temperature_max_c=daily_maximums[index]
                if index < len(daily_maximums)
                else None,
                precipitation_total=daily_precipitation[index]
                if index < len(daily_precipitation)
                else None,
                precipitation_snow=daily_snowfall[index]
                if index < len(daily_snowfall)
                else None,
                cloud_cover=(
                    sum(day_clouds) / len(day_clouds) if day_clouds else None
                ),
            )
        )

    return ProviderForecast(
        provider="open_meteo",
        latitude=data["latitude"],
        longitude=data["longitude"],
        timezone=data["timezone"],
        forecast=points,
        daily_forecast=daily_points,
    )

async def obtain_open_meteo_forecast(
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
