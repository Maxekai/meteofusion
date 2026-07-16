import unittest
from unittest.mock import patch

from app.models.weather import ForecastPoint, ProviderForecast
from app.providers.exceptions import WeatherProviderError
from app.services.consensus_weather_service import obtain_aggregated_weather_forecast


BARCELONA_LATITUDE = 41.3874
BARCELONA_LONGITUDE = 2.1686


def _build_provider_forecast(
    provider: str,
    first_hour_temperature: float,
    second_hour_temperature: float,
    first_hour_probability: float,
    second_hour_probability: float,
    second_hour_precipitation: float,
    first_hour_cloud_cover: float,
    second_hour_cloud_cover: float,
    first_hour_humidity: float,
    second_hour_humidity: float,
    first_hour_wind: float,
    second_hour_wind: float,
    first_hour_apparent_temperature: float,
    second_hour_apparent_temperature: float,
) -> ProviderForecast:
    return ProviderForecast(
        provider=provider,
        latitude=BARCELONA_LATITUDE,
        longitude=BARCELONA_LONGITUDE,
        timezone="Europe/Madrid",
        forecast=[
            ForecastPoint(
                datetime="2026-07-12T00:00:00",
                temperature_c=first_hour_temperature,
                humidity_percent=first_hour_humidity,
                precipitation_probability=first_hour_probability,
                precipitation_total=0.0,
                precipitation_snow=0.0,
                cloud_cover=first_hour_cloud_cover,
                wind_speed_kmh=first_hour_wind,
                apparent_temperature_c=first_hour_apparent_temperature,
            ),
            ForecastPoint(
                datetime="2026-07-12T01:00:00",
                temperature_c=second_hour_temperature,
                humidity_percent=second_hour_humidity,
                precipitation_probability=second_hour_probability,
                precipitation_total=second_hour_precipitation,
                precipitation_snow=0.0,
                cloud_cover=second_hour_cloud_cover,
                wind_speed_kmh=second_hour_wind,
                apparent_temperature_c=second_hour_apparent_temperature,
            ),
        ],
    )


class ConsensusWeatherServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_obtain_aggregated_weather_forecast_uses_common_hour_overlap(
        self,
    ) -> None:
        async def fake_google_weather(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            return ProviderForecast(
                provider="google_weather",
                latitude=latitude,
                longitude=longitude,
                timezone="+02:00",
                forecast=[
                    ForecastPoint(
                        datetime="2026-07-12T07:00:00Z",
                        temperature_c=30.0,
                        humidity_percent=50.0,
                        precipitation_probability=0.0,
                        precipitation_total=0.0,
                        precipitation_snow=0.0,
                        cloud_cover=10.0,
                        wind_speed_kmh=12.0,
                        apparent_temperature_c=31.0,
                    ),
                    ForecastPoint(
                        datetime="2026-07-12T08:00:00Z",
                        temperature_c=31.0,
                        humidity_percent=48.0,
                        precipitation_probability=0.0,
                        precipitation_total=0.0,
                        precipitation_snow=0.0,
                        cloud_cover=5.0,
                        wind_speed_kmh=13.0,
                        apparent_temperature_c=32.0,
                    ),
                ],
            )

        async def fake_open_meteo(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            return ProviderForecast(
                provider="open_meteo",
                latitude=latitude,
                longitude=longitude,
                timezone="Europe/Madrid",
                forecast=[
                    ForecastPoint(
                        datetime="2026-07-12T00:00:00",
                        temperature_c=24.0,
                        humidity_percent=75.0,
                        precipitation_probability=0.0,
                        precipitation_total=0.0,
                        precipitation_snow=0.0,
                        cloud_cover=60.0,
                        wind_speed_kmh=5.0,
                        apparent_temperature_c=26.0,
                    ),
                    ForecastPoint(
                        datetime="2026-07-12T09:00:00",
                        temperature_c=29.0,
                        humidity_percent=55.0,
                        precipitation_probability=0.0,
                        precipitation_total=0.0,
                        precipitation_snow=0.0,
                        cloud_cover=20.0,
                        wind_speed_kmh=10.0,
                        apparent_temperature_c=30.0,
                    ),
                    ForecastPoint(
                        datetime="2026-07-12T10:00:00",
                        temperature_c=30.0,
                        humidity_percent=52.0,
                        precipitation_probability=0.0,
                        precipitation_total=0.0,
                        precipitation_snow=0.0,
                        cloud_cover=15.0,
                        wind_speed_kmh=11.0,
                        apparent_temperature_c=31.0,
                    ),
                ],
            )

        async def fake_weather_api(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            return ProviderForecast(
                provider="weather_api",
                latitude=latitude,
                longitude=longitude,
                timezone="Europe/Madrid",
                forecast=[
                    ForecastPoint(
                        datetime="2026-07-12T00:00:00",
                        temperature_c=25.0,
                        humidity_percent=72.0,
                        precipitation_probability=5.0,
                        precipitation_total=0.0,
                        precipitation_snow=0.0,
                        cloud_cover=55.0,
                        wind_speed_kmh=6.0,
                        apparent_temperature_c=26.5,
                    ),
                    ForecastPoint(
                        datetime="2026-07-12T09:00:00",
                        temperature_c=30.0,
                        humidity_percent=54.0,
                        precipitation_probability=5.0,
                        precipitation_total=0.0,
                        precipitation_snow=0.0,
                        cloud_cover=18.0,
                        wind_speed_kmh=11.0,
                        apparent_temperature_c=31.0,
                    ),
                    ForecastPoint(
                        datetime="2026-07-12T10:00:00",
                        temperature_c=31.0,
                        humidity_percent=50.0,
                        precipitation_probability=5.0,
                        precipitation_total=0.0,
                        precipitation_snow=0.0,
                        cloud_cover=10.0,
                        wind_speed_kmh=12.0,
                        apparent_temperature_c=32.0,
                    ),
                ],
            )

        with patch(
            "app.services.consensus_weather_service.obtain_google_weather_forecast",
            new=fake_google_weather,
        ), patch(
            "app.services.consensus_weather_service.obtain_open_meteo_forecast",
            new=fake_open_meteo,
        ), patch(
            "app.services.consensus_weather_service.obtain_weather_api_forecast",
            new=fake_weather_api,
        ):
            aggregated_forecast = await obtain_aggregated_weather_forecast(
                latitude=BARCELONA_LATITUDE,
                longitude=BARCELONA_LONGITUDE,
                days=7,
            )

        self.assertEqual(
            [point.datetime.isoformat() for point in aggregated_forecast.hourly_forecast],
            ["2026-07-12T09:00:00", "2026-07-12T10:00:00"],
        )
        self.assertEqual(
            aggregated_forecast.hourly_window.mode,
            "common_provider_overlap",
        )
        self.assertEqual(
            aggregated_forecast.hourly_window.start.isoformat(),
            "2026-07-12T09:00:00",
        )
        self.assertEqual(
            aggregated_forecast.hourly_window.end.isoformat(),
            "2026-07-12T10:00:00",
        )
        self.assertEqual(
            aggregated_forecast.daily_window.mode,
            "common_provider_overlap",
        )
        self.assertEqual(
            aggregated_forecast.daily_window.start.isoformat(),
            "2026-07-12",
        )
        self.assertEqual(
            aggregated_forecast.daily_window.end.isoformat(),
            "2026-07-12",
        )
        self.assertTrue(
            all(point.provider_count == 3 for point in aggregated_forecast.hourly_forecast)
        )
        self.assertEqual(len(aggregated_forecast.daily_forecast), 1)
        self.assertEqual(aggregated_forecast.daily_forecast[0].provider_count, 3)

    async def test_obtain_aggregated_weather_forecast_computes_hourly_and_daily_stats(
        self,
    ) -> None:
        async def fake_google_weather(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            self.assertEqual(latitude, BARCELONA_LATITUDE)
            self.assertEqual(longitude, BARCELONA_LONGITUDE)
            self.assertEqual(days, 7)
            return _build_provider_forecast(
                provider="google_weather",
                first_hour_temperature=22.0,
                second_hour_temperature=17.0,
                first_hour_probability=20.0,
                second_hour_probability=70.0,
                second_hour_precipitation=2.0,
                first_hour_cloud_cover=20.0,
                second_hour_cloud_cover=80.0,
                first_hour_humidity=55.0,
                second_hour_humidity=68.0,
                first_hour_wind=6.0,
                second_hour_wind=8.0,
                first_hour_apparent_temperature=22.0,
                second_hour_apparent_temperature=16.0,
            )

        async def fake_open_meteo(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            self.assertEqual(latitude, BARCELONA_LATITUDE)
            self.assertEqual(longitude, BARCELONA_LONGITUDE)
            self.assertEqual(days, 7)
            return _build_provider_forecast(
                provider="open_meteo",
                first_hour_temperature=20.0,
                second_hour_temperature=18.0,
                first_hour_probability=10.0,
                second_hour_probability=80.0,
                second_hour_precipitation=3.0,
                first_hour_cloud_cover=10.0,
                second_hour_cloud_cover=90.0,
                first_hour_humidity=60.0,
                second_hour_humidity=70.0,
                first_hour_wind=5.0,
                second_hour_wind=7.0,
                first_hour_apparent_temperature=20.0,
                second_hour_apparent_temperature=17.0,
            )

        async def fake_weather_api(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            self.assertEqual(latitude, BARCELONA_LATITUDE)
            self.assertEqual(longitude, BARCELONA_LONGITUDE)
            self.assertEqual(days, 7)
            return _build_provider_forecast(
                provider="weather_api",
                first_hour_temperature=21.0,
                second_hour_temperature=16.0,
                first_hour_probability=30.0,
                second_hour_probability=90.0,
                second_hour_precipitation=4.0,
                first_hour_cloud_cover=30.0,
                second_hour_cloud_cover=95.0,
                first_hour_humidity=58.0,
                second_hour_humidity=72.0,
                first_hour_wind=4.0,
                second_hour_wind=10.0,
                first_hour_apparent_temperature=21.0,
                second_hour_apparent_temperature=15.0,
            )

        with patch(
            "app.services.consensus_weather_service.obtain_google_weather_forecast",
            new=fake_google_weather,
        ), patch(
            "app.services.consensus_weather_service.obtain_open_meteo_forecast",
            new=fake_open_meteo,
        ), patch(
            "app.services.consensus_weather_service.obtain_weather_api_forecast",
            new=fake_weather_api,
        ):
            aggregated_forecast = await obtain_aggregated_weather_forecast(
                latitude=BARCELONA_LATITUDE,
                longitude=BARCELONA_LONGITUDE,
                days=7,
            )

        self.assertEqual(aggregated_forecast.days, 7)
        self.assertEqual(
            aggregated_forecast.providers_used,
            ["google_weather", "open_meteo", "weather_api"],
        )
        self.assertEqual(
            aggregated_forecast.hourly_window.mode,
            "common_provider_overlap",
        )
        self.assertEqual(
            aggregated_forecast.hourly_window.start.isoformat(),
            "2026-07-12T00:00:00",
        )
        self.assertEqual(
            aggregated_forecast.hourly_window.end.isoformat(),
            "2026-07-12T01:00:00",
        )
        self.assertEqual(
            aggregated_forecast.daily_window.mode,
            "common_provider_overlap",
        )
        self.assertEqual(
            aggregated_forecast.daily_window.start.isoformat(),
            "2026-07-12",
        )
        self.assertEqual(
            aggregated_forecast.daily_window.end.isoformat(),
            "2026-07-12",
        )
        self.assertEqual(len(aggregated_forecast.hourly_forecast), 2)
        self.assertEqual(len(aggregated_forecast.daily_forecast), 1)
        self.assertEqual(aggregated_forecast.warnings, [])

        first_hour = aggregated_forecast.hourly_forecast[0]
        second_hour = aggregated_forecast.hourly_forecast[1]
        first_day = aggregated_forecast.daily_forecast[0]

        self.assertEqual(first_hour.condition, "sunny")
        self.assertEqual(first_hour.temperature_c.min, 20.0)
        self.assertEqual(first_hour.temperature_c.avg, 21.0)
        self.assertEqual(first_hour.temperature_c.max, 22.0)
        self.assertEqual(first_hour.precipitation_probability.avg, 20.0)
        self.assertEqual(first_hour.humidity_percent, 57.67)
        self.assertEqual(first_hour.wind_speed_kmh, 5.0)

        self.assertEqual(second_hour.condition, "rain")
        self.assertEqual(second_hour.temperature_c.min, 16.0)
        self.assertEqual(second_hour.temperature_c.avg, 17.0)
        self.assertEqual(second_hour.temperature_c.max, 18.0)
        self.assertEqual(second_hour.precipitation_probability.avg, 80.0)
        self.assertEqual(second_hour.precipitation_total.min, 2.0)
        self.assertEqual(second_hour.precipitation_total.avg, 3.0)
        self.assertEqual(second_hour.precipitation_total.max, 4.0)

        self.assertEqual(str(first_day.date), "2026-07-12")
        self.assertEqual(first_day.condition, "rain")
        self.assertEqual(first_day.temperature_min_c.min, 16.0)
        self.assertEqual(first_day.temperature_min_c.avg, 17.0)
        self.assertEqual(first_day.temperature_min_c.max, 18.0)
        self.assertEqual(first_day.temperature_max_c.min, 20.0)
        self.assertEqual(first_day.temperature_max_c.avg, 21.0)
        self.assertEqual(first_day.temperature_max_c.max, 22.0)
        self.assertEqual(first_day.precipitation_total.min, 2.0)
        self.assertEqual(first_day.precipitation_total.avg, 3.0)
        self.assertEqual(first_day.precipitation_total.max, 4.0)

    async def test_obtain_aggregated_weather_forecast_keeps_partial_results(self) -> None:
        async def fake_google_weather(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            return _build_provider_forecast(
                provider="google_weather",
                first_hour_temperature=22.0,
                second_hour_temperature=17.0,
                first_hour_probability=20.0,
                second_hour_probability=70.0,
                second_hour_precipitation=2.0,
                first_hour_cloud_cover=20.0,
                second_hour_cloud_cover=80.0,
                first_hour_humidity=55.0,
                second_hour_humidity=68.0,
                first_hour_wind=6.0,
                second_hour_wind=8.0,
                first_hour_apparent_temperature=22.0,
                second_hour_apparent_temperature=16.0,
            )

        async def fake_open_meteo(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            raise WeatherProviderError("Open-Meteo fuera de servicio")

        async def fake_weather_api(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            return _build_provider_forecast(
                provider="weather_api",
                first_hour_temperature=21.0,
                second_hour_temperature=16.0,
                first_hour_probability=30.0,
                second_hour_probability=90.0,
                second_hour_precipitation=4.0,
                first_hour_cloud_cover=30.0,
                second_hour_cloud_cover=95.0,
                first_hour_humidity=58.0,
                second_hour_humidity=72.0,
                first_hour_wind=4.0,
                second_hour_wind=10.0,
                first_hour_apparent_temperature=21.0,
                second_hour_apparent_temperature=15.0,
            )

        with patch(
            "app.services.consensus_weather_service.obtain_google_weather_forecast",
            new=fake_google_weather,
        ), patch(
            "app.services.consensus_weather_service.obtain_open_meteo_forecast",
            new=fake_open_meteo,
        ), patch(
            "app.services.consensus_weather_service.obtain_weather_api_forecast",
            new=fake_weather_api,
        ):
            aggregated_forecast = await obtain_aggregated_weather_forecast(
                latitude=BARCELONA_LATITUDE,
                longitude=BARCELONA_LONGITUDE,
                days=7,
            )

        self.assertEqual(
            aggregated_forecast.providers_used,
            ["google_weather", "weather_api"],
        )
        self.assertEqual(
            aggregated_forecast.hourly_window.mode,
            "common_provider_overlap",
        )
        self.assertEqual(
            aggregated_forecast.hourly_window.start.isoformat(),
            "2026-07-12T00:00:00",
        )
        self.assertEqual(
            aggregated_forecast.hourly_window.end.isoformat(),
            "2026-07-12T01:00:00",
        )
        self.assertEqual(
            aggregated_forecast.daily_window.mode,
            "common_provider_overlap",
        )
        self.assertEqual(
            aggregated_forecast.daily_window.start.isoformat(),
            "2026-07-12",
        )
        self.assertEqual(
            aggregated_forecast.daily_window.end.isoformat(),
            "2026-07-12",
        )
        self.assertEqual(
            aggregated_forecast.provider_errors,
            {"open_meteo": "Open-Meteo fuera de servicio"},
        )
        self.assertIn(
            "La agregacion se ha calculado con los proveedores disponibles.",
            aggregated_forecast.warnings,
        )


if __name__ == "__main__":
    unittest.main()
