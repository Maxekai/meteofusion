import asyncio
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Awaitable, Callable, Iterable, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd

from app.models.weather import (
    AggregatedDailyForecastPoint,
    AggregatedForecast,
    AggregatedHourlyForecastPoint,
    AggregatedStat,
    AggregationWindow,
    DailyAggregationWindow,
    ForecastPoint,
    ProviderDailyForecastPoint,
    ProviderForecast,
)
from app.providers.exceptions import WeatherProviderError
from app.services.google_weather_service import obtain_google_weather_forecast
from app.services.meteosource_service import obtain_meteosource_forecast
from app.services.open_meteo_service import obtain_open_meteo_forecast
from app.services.openweather_service import obtain_openweather_forecast
from app.services.weather_api import obtain_weather_api_forecast
from app.services.xweather_service import obtain_xweather_forecast


CONDITION_PRIORITY = {
    "snow": 5,
    "rain": 4,
    "cloudy": 3,
    "partly_cloudy": 2,
    "sunny": 1,
    "unknown": 0,
}
OFFSET_TIMEZONE_PATTERN = re.compile(r"^[+-]\d{2}:\d{2}$")


@dataclass(frozen=True)
class HourlyWindowResult:
    provider_forecasts: list[ProviderForecast]
    mode: str
    start: Optional[datetime]
    end: Optional[datetime]


def _get_provider_fetchers() -> dict[
    str,
    Callable[[float, float, int], Awaitable[ProviderForecast]],
]:
    return {
        "google_weather": obtain_google_weather_forecast,
        "meteosource": obtain_meteosource_forecast,
        "open_meteo": obtain_open_meteo_forecast,
        "openweather": obtain_openweather_forecast,
        "weather_api": obtain_weather_api_forecast,
        "xweather": obtain_xweather_forecast,
    }


def _round_value(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None

    return round(value, 2)


def _build_stat(values: pd.Series) -> AggregatedStat:
    numeric_values = pd.to_numeric(values, errors="coerce").dropna()
    if numeric_values.empty:
        return AggregatedStat()

    return AggregatedStat(
        min=_round_value(float(numeric_values.min())),
        avg=_round_value(float(numeric_values.mean())),
        max=_round_value(float(numeric_values.max())),
    )


def _build_mean(values: pd.Series) -> Optional[float]:
    numeric_values = pd.to_numeric(values, errors="coerce").dropna()
    if numeric_values.empty:
        return None

    return _round_value(float(numeric_values.mean()))


def _parse_timezone(timezone_name: str) -> Optional[tzinfo]:
    if not timezone_name:
        return None

    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        pass

    if not OFFSET_TIMEZONE_PATTERN.match(timezone_name):
        return None

    sign = 1 if timezone_name.startswith("+") else -1
    hours, minutes = timezone_name[1:].split(":")
    offset = timedelta(
        hours=sign * int(hours),
        minutes=sign * int(minutes),
    )
    return timezone(offset)


def _normalize_datetime(value: datetime, timezone_name: str) -> datetime:
    if value.tzinfo is None:
        return value.replace(minute=0, second=0, microsecond=0)

    parsed_timezone = _parse_timezone(timezone_name)
    localized = value.astimezone(parsed_timezone) if parsed_timezone else value
    return localized.replace(
        tzinfo=None,
        minute=0,
        second=0,
        microsecond=0,
    )


def _classify_condition(point: ForecastPoint) -> str:
    snow_amount = float(point.precipitation_snow or 0.0)
    precipitation_amount = float(point.precipitation_total or 0.0)
    precipitation_probability = float(point.precipitation_probability or 0.0)
    cloud_cover = point.cloud_cover

    if snow_amount > 0.0:
        return "snow"

    if precipitation_amount > 0.1 or precipitation_probability >= 60.0:
        return "rain"

    if cloud_cover is None:
        return "unknown"

    if cloud_cover >= 70.0:
        return "cloudy"

    if cloud_cover >= 35.0:
        return "partly_cloudy"

    return "sunny"


def _classify_daily_condition(point: ProviderDailyForecastPoint) -> str:
    snow_amount = float(point.precipitation_snow or 0.0)
    precipitation_amount = float(point.precipitation_total or 0.0)
    cloud_cover = point.cloud_cover

    if snow_amount > 0.0:
        return "snow"

    if precipitation_amount > 0.1:
        return "rain"

    if cloud_cover is None:
        return "unknown"

    if cloud_cover >= 70.0:
        return "cloudy"

    if cloud_cover >= 35.0:
        return "partly_cloudy"

    return "sunny"


def _consensus_condition(conditions: Iterable[str]) -> str:
    filtered_conditions = [condition for condition in conditions if condition != "unknown"]
    if not filtered_conditions:
        return "unknown"

    condition_counts = Counter(filtered_conditions)
    highest_count = max(condition_counts.values())
    candidates = [
        condition
        for condition, count in condition_counts.items()
        if count == highest_count
    ]
    return max(
        candidates,
        key=lambda condition: CONDITION_PRIORITY.get(condition, 0),
    )


def _most_common_timezone(provider_forecasts: list[ProviderForecast]) -> str:
    timezone_counts = Counter(
        forecast.timezone
        for forecast in provider_forecasts
        if forecast.timezone
    )
    if not timezone_counts:
        return "UTC"

    return timezone_counts.most_common(1)[0][0]


FORECAST_COLUMNS = [
    "provider",
    "datetime",
    "temperature_c",
    "precipitation_probability",
    "precipitation_total",
    "precipitation_snow",
    "humidity_percent",
    "cloud_cover",
    "wind_speed_kmh",
    "apparent_temperature_c",
    "condition",
]


def _provider_forecasts_to_dataframe(
    provider_forecasts: list[ProviderForecast],
) -> pd.DataFrame:
    records = []

    for provider_forecast in provider_forecasts:
        for point in provider_forecast.forecast:
            records.append(
                {
                    "provider": provider_forecast.provider,
                    "datetime": _normalize_datetime(
                        value=point.datetime,
                        timezone_name=provider_forecast.timezone,
                    ),
                    "temperature_c": point.temperature_c,
                    "precipitation_probability": point.precipitation_probability,
                    "precipitation_total": point.precipitation_total,
                    "precipitation_snow": point.precipitation_snow,
                    "humidity_percent": point.humidity_percent,
                    "cloud_cover": point.cloud_cover,
                    "wind_speed_kmh": point.wind_speed_kmh,
                    "apparent_temperature_c": point.apparent_temperature_c,
                    "condition": _classify_condition(point),
                }
            )

    dataframe = pd.DataFrame.from_records(records, columns=FORECAST_COLUMNS)
    if not dataframe.empty:
        dataframe["datetime"] = pd.to_datetime(dataframe["datetime"])

    return dataframe


def _aggregate_hourly(
    provider_forecasts: list[ProviderForecast],
) -> list[AggregatedHourlyForecastPoint]:
    dataframe = _provider_forecasts_to_dataframe(provider_forecasts)
    if dataframe.empty:
        return []

    aggregated_points: list[AggregatedHourlyForecastPoint] = []

    for forecast_hour, hourly_data in dataframe.groupby("datetime", sort=True):
        aggregated_points.append(
            AggregatedHourlyForecastPoint(
                datetime=forecast_hour.to_pydatetime(),
                provider_count=len(hourly_data),
                temperature_c=_build_stat(hourly_data["temperature_c"]),
                precipitation_probability=_build_stat(
                    hourly_data["precipitation_probability"]
                ),
                precipitation_total=_build_stat(hourly_data["precipitation_total"]),
                precipitation_snow=_build_stat(hourly_data["precipitation_snow"]),
                humidity_percent=_build_mean(hourly_data["humidity_percent"]),
                cloud_cover=_build_mean(hourly_data["cloud_cover"]),
                wind_speed_kmh=_build_mean(hourly_data["wind_speed_kmh"]),
                apparent_temperature_c=_build_mean(
                    hourly_data["apparent_temperature_c"]
                ),
                condition=_consensus_condition(hourly_data["condition"]),
            )
        )

    return aggregated_points


def _filter_to_common_hour_range(
    provider_forecasts: list[ProviderForecast],
) -> HourlyWindowResult:
    if not provider_forecasts:
        return HourlyWindowResult(
            provider_forecasts=[],
            mode="empty",
            start=None,
            end=None,
        )

    provider_ranges: list[tuple[datetime, datetime]] = []

    for provider_forecast in provider_forecasts:
        normalized_hours = [
            _normalize_datetime(
                value=point.datetime,
                timezone_name=provider_forecast.timezone,
            )
            for point in provider_forecast.forecast
        ]
        if not normalized_hours:
            continue

        provider_ranges.append((min(normalized_hours), max(normalized_hours)))

    if not provider_ranges:
        return HourlyWindowResult(
            provider_forecasts=provider_forecasts,
            mode="empty",
            start=None,
            end=None,
        )

    if len(provider_ranges) <= 1:
        start, end = provider_ranges[0]
        return HourlyWindowResult(
            provider_forecasts=provider_forecasts,
            mode="single_provider_range",
            start=start,
            end=end,
        )

    common_start = max(start for start, _ in provider_ranges)
    common_end = min(end for _, end in provider_ranges)
    # Preserve the horizon while excluding tails backed by only a minority.
    required_provider_count = len(provider_ranges) // 2 + 1
    consensus_start = sorted(
        start for start, _ in provider_ranges
    )[required_provider_count - 1]
    consensus_end = sorted(
        (end for _, end in provider_ranges),
        reverse=True,
    )[required_provider_count - 1]

    if consensus_start > consensus_end:
        return HourlyWindowResult(
            provider_forecasts=provider_forecasts,
            mode="available_provider_union",
            start=min(start for start, _ in provider_ranges),
            end=max(end for _, end in provider_ranges),
        )

    window_mode = (
        "common_provider_overlap"
        if common_start == consensus_start and common_end == consensus_end
        else "available_provider_union"
    )
    filtered_forecasts: list[ProviderForecast] = []

    for provider_forecast in provider_forecasts:
        filtered_points = [
            point
            for point in provider_forecast.forecast
            if consensus_start
            <= _normalize_datetime(
                value=point.datetime,
                timezone_name=provider_forecast.timezone,
            )
            <= consensus_end
        ]
        filtered_forecasts.append(
            provider_forecast.model_copy(update={"forecast": filtered_points})
        )

    return HourlyWindowResult(
        provider_forecasts=filtered_forecasts,
        mode=window_mode,
        start=consensus_start,
        end=consensus_end,
    )


DAILY_FORECAST_COLUMNS = [
    "provider",
    "date",
    "temperature_min_c",
    "temperature_max_c",
    "precipitation_total",
    "condition",
]


def _provider_forecasts_to_daily_dataframe(
    provider_forecasts: list[ProviderForecast],
) -> pd.DataFrame:
    records: list[dict[str, object]] = []

    for provider_forecast in provider_forecasts:
        if provider_forecast.daily_forecast:
            for point in provider_forecast.daily_forecast:
                records.append(
                    {
                        "provider": provider_forecast.provider,
                        "date": point.date,
                        "temperature_min_c": point.temperature_min_c,
                        "temperature_max_c": point.temperature_max_c,
                        "precipitation_total": point.precipitation_total,
                        "condition": _classify_daily_condition(point),
                    }
                )
            continue

        dataframe = _provider_forecasts_to_dataframe([provider_forecast])
        if dataframe.empty:
            continue

        dataframe["date"] = dataframe["datetime"].dt.date
        provider_daily = (
            dataframe.groupby(["provider", "date"], as_index=False, sort=True)
            .agg(
                temperature_min_c=("temperature_c", "min"),
                temperature_max_c=("temperature_c", "max"),
                precipitation_total=(
                    "precipitation_total",
                    lambda values: values.sum(min_count=1),
                ),
                condition=("condition", _consensus_condition),
            )
        )
        records.extend(provider_daily.to_dict(orient="records"))

    return pd.DataFrame.from_records(records, columns=DAILY_FORECAST_COLUMNS)


def _aggregate_daily(
    provider_forecasts: list[ProviderForecast],
) -> list[AggregatedDailyForecastPoint]:
    provider_daily = _provider_forecasts_to_daily_dataframe(provider_forecasts)
    if provider_daily.empty:
        return []

    aggregated_days: list[AggregatedDailyForecastPoint] = []

    for forecast_date, daily_data in provider_daily.groupby("date", sort=True):
        aggregated_days.append(
            AggregatedDailyForecastPoint(
                date=forecast_date,
                provider_count=len(daily_data),
                temperature_min_c=_build_stat(daily_data["temperature_min_c"]),
                temperature_max_c=_build_stat(daily_data["temperature_max_c"]),
                precipitation_total=_build_stat(daily_data["precipitation_total"]),
                condition=_consensus_condition(daily_data["condition"]),
            )
        )

    return aggregated_days


def _build_daily_window(
    daily_forecast: list[AggregatedDailyForecastPoint],
    mode: str,
) -> DailyAggregationWindow:
    if not daily_forecast:
        return DailyAggregationWindow(
            mode=mode,
            start=None,
            end=None,
        )

    return DailyAggregationWindow(
        mode=mode,
        start=daily_forecast[0].date,
        end=daily_forecast[-1].date,
    )


async def obtain_aggregated_weather_forecast(
    latitude: float,
    longitude: float,
    days: int = 7,
) -> AggregatedForecast:
    provider_fetchers = _get_provider_fetchers()
    provider_names = list(provider_fetchers.keys())
    provider_calls = [
        provider_fetcher(
            latitude=latitude,
            longitude=longitude,
            days=days,
        )
        for provider_fetcher in provider_fetchers.values()
    ]
    provider_results = await asyncio.gather(*provider_calls, return_exceptions=True)

    provider_forecasts: list[ProviderForecast] = []
    provider_errors: dict[str, str] = {}

    for provider_name, result in zip(provider_names, provider_results):
        if isinstance(result, Exception):
            provider_errors[provider_name] = str(result)
            continue

        provider_forecasts.append(result)

    if not provider_forecasts:
        raise WeatherProviderError(
            "No se ha podido obtener la prediccion de ningun proveedor."
        )

    daily_forecast = _aggregate_daily(provider_forecasts)[:days]
    hourly_window = _filter_to_common_hour_range(provider_forecasts)
    provider_forecasts = hourly_window.provider_forecasts

    warnings: list[str] = []

    if provider_errors:
        warnings.append(
            "La agregacion se ha calculado con los proveedores disponibles."
        )

    return AggregatedForecast(
        latitude=latitude,
        longitude=longitude,
        timezone=_most_common_timezone(provider_forecasts),
        days=days,
        providers_requested=provider_names,
        providers_used=[forecast.provider for forecast in provider_forecasts],
        provider_errors=provider_errors,
        warnings=warnings,
        hourly_window=AggregationWindow(
            mode=hourly_window.mode,
            start=hourly_window.start,
            end=hourly_window.end,
        ),
        daily_window=_build_daily_window(
            daily_forecast=daily_forecast,
            mode=hourly_window.mode,
        ),
        hourly_forecast=_aggregate_hourly(provider_forecasts),
        daily_forecast=daily_forecast,
    )
