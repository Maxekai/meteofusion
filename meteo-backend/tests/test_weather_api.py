import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from app.models.weather import (
    AggregatedDailyForecastPoint,
    AggregatedForecast,
    AggregatedHourlyForecastPoint,
    AggregatedStat,
    AggregationWindow,
    DailyAggregationWindow,
    ForecastPoint,
    ProviderForecast,
)


client = TestClient(app)
BARCELONA_LATITUDE = 41.3874
BARCELONA_LONGITUDE = 2.1686
RUN_REAL_OPEN_METEO_TESTS = os.getenv("RUN_REAL_OPEN_METEO_TESTS") in {
    "1",
    "true",
    "TRUE",
}


class WeatherApiTestCase(unittest.TestCase):
    def test_get_aggregated_forecast_returns_consensus_payload(self) -> None:
        async def fake_obtain_aggregated_weather_forecast(
            latitude: float,
            longitude: float,
            days: int,
        ) -> AggregatedForecast:
            self.assertEqual(latitude, BARCELONA_LATITUDE)
            self.assertEqual(longitude, BARCELONA_LONGITUDE)
            self.assertEqual(days, 7)
            return AggregatedForecast(
                latitude=latitude,
                longitude=longitude,
                timezone="Europe/Madrid",
                days=days,
                providers_requested=[
                    "google_weather",
                    "open_meteo",
                    "weather_api",
                ],
                providers_used=[
                    "google_weather",
                    "open_meteo",
                    "weather_api",
                ],
                warnings=[],
                hourly_window=AggregationWindow(
                    mode="common_provider_overlap",
                    start="2026-07-12T10:00:00",
                    end="2026-07-12T10:00:00",
                ),
                daily_window=DailyAggregationWindow(
                    mode="common_provider_overlap",
                    start="2026-07-12",
                    end="2026-07-12",
                ),
                hourly_forecast=[
                    AggregatedHourlyForecastPoint(
                        datetime="2026-07-12T10:00",
                        provider_count=3,
                        temperature_c=AggregatedStat(min=20.0, avg=21.0, max=22.0),
                        precipitation_probability=AggregatedStat(
                            min=5.0,
                            avg=10.0,
                            max=15.0,
                        ),
                        precipitation_total=AggregatedStat(
                            min=0.0,
                            avg=0.2,
                            max=0.4,
                        ),
                        precipitation_snow=AggregatedStat(
                            min=0.0,
                            avg=0.0,
                            max=0.0,
                        ),
                        humidity_percent=55.0,
                        cloud_cover=25.0,
                        wind_speed_kmh=12.0,
                        dew_point_c=14.0,
                        apparent_temperature_c=21.5,
                        condition="sunny",
                    )
                ],
                daily_forecast=[
                    AggregatedDailyForecastPoint(
                        date="2026-07-12",
                        provider_count=3,
                        temperature_min_c=AggregatedStat(
                            min=16.0,
                            avg=17.0,
                            max=18.0,
                        ),
                        temperature_max_c=AggregatedStat(
                            min=28.0,
                            avg=29.0,
                            max=30.0,
                        ),
                        precipitation_total=AggregatedStat(
                            min=1.0,
                            avg=2.0,
                            max=3.0,
                        ),
                        condition="sunny",
                    )
                ],
            )

        with patch(
            "app.api.weather.obtain_aggregated_weather_forecast",
            new=fake_obtain_aggregated_weather_forecast,
        ):
            response = client.get(
                "/api/weather/aggregate/forecast",
                params={
                    "latitude": BARCELONA_LATITUDE,
                    "longitude": BARCELONA_LONGITUDE,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["days"], 7)
        self.assertEqual(
            response.json()["providers_used"],
            ["google_weather", "open_meteo", "weather_api"],
        )
        self.assertEqual(
            response.json()["hourly_window"]["mode"],
            "common_provider_overlap",
        )
        self.assertEqual(
            response.json()["daily_window"],
            {
                "mode": "common_provider_overlap",
                "start": "2026-07-12",
                "end": "2026-07-12",
            },
        )
        self.assertEqual(response.json()["hourly_forecast"][0]["condition"], "sunny")
        self.assertEqual(response.json()["daily_forecast"][0]["condition"], "sunny")

    def test_get_forecast_returns_normalized_payload(self) -> None:
        async def fake_obtain_open_meteo_forecast(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            self.assertEqual(latitude, 40.4168)
            self.assertEqual(longitude, -3.7038)
            self.assertEqual(days, 2)
            return ProviderForecast(
                provider="open_meteo",
                latitude=latitude,
                longitude=longitude,
                timezone="Europe/Madrid",
                forecast=[
                    ForecastPoint(
                        datetime="2026-06-15T12:00",
                        temperature_c=28.5,
                        humidity_percent=35,
                        precipitation_probability=10,
                        cloud_cover=42,
                        wind_speed_kmh=14.2,
                        dew_point_c=18.4,
                        apparent_temperature_c=30.1,
                        precipitation_total=1.2,
                        precipitation_snow=0.0,
                    )
                ],
            )

        with patch(
            "app.api.weather.obtain_open_meteo_forecast",
            new=fake_obtain_open_meteo_forecast,
        ):
            response = client.get(
                "/api/weather/open_meteo/forecast",
                params={
                    "latitude": 40.4168,
                    "longitude": -3.7038,
                    "days": 2,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "provider": "open_meteo",
                "latitude": 40.4168,
                "longitude": -3.7038,
                "timezone": "Europe/Madrid",
                "forecast": [
                    {
                        "datetime": "2026-06-15T12:00:00",
                        "temperature_c": 28.5,
                        "humidity_percent": 35.0,
                        "precipitation_probability": 10.0,
                        "cloud_cover": 42.0,
                        "wind_speed_kmh": 14.2,
                        "dew_point_c": 18.4,
                        "apparent_temperature_c": 30.1,
                        "precipitation_total": 1.2,
                        "precipitation_snow": 0.0,
                    }
                ],
            },
        )

    def test_get_forecast_routes_to_weather_api_provider(self) -> None:
        async def fake_obtain_weather_api_forecast(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            self.assertEqual(latitude, BARCELONA_LATITUDE)
            self.assertEqual(longitude, BARCELONA_LONGITUDE)
            self.assertEqual(days, 1)
            return ProviderForecast(
                provider="weather_api",
                latitude=latitude,
                longitude=longitude,
                timezone="Europe/Madrid",
                forecast=[
                    ForecastPoint(
                        datetime="2026-06-15T13:00",
                        temperature_c=27.1,
                        humidity_percent=60,
                        precipitation_probability=15,
                        cloud_cover=35,
                        wind_speed_kmh=12.0,
                        dew_point_c=18.0,
                        apparent_temperature_c=28.3,
                        precipitation_total=0.2,
                        precipitation_snow=0.0,
                    )
                ],
            )

        with patch(
            "app.api.weather.obtain_weather_api_forecast",
            new=fake_obtain_weather_api_forecast,
        ):
            response = client.get(
                "/api/weather/weather_api/forecast",
                params={
                    "latitude": BARCELONA_LATITUDE,
                    "longitude": BARCELONA_LONGITUDE,
                    "days": 1,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider"], "weather_api")
        self.assertGreater(len(response.json()["forecast"]), 0)

    def test_get_forecast_routes_to_google_weather_provider(self) -> None:
        async def fake_obtain_google_weather_forecast(
            latitude: float,
            longitude: float,
            days: int,
        ) -> ProviderForecast:
            self.assertEqual(latitude, BARCELONA_LATITUDE)
            self.assertEqual(longitude, BARCELONA_LONGITUDE)
            self.assertEqual(days, 1)
            return ProviderForecast(
                provider="google_weather",
                latitude=latitude,
                longitude=longitude,
                timezone="Europe/Madrid",
                forecast=[
                    ForecastPoint(
                        datetime="2026-06-15T14:00:00Z",
                        temperature_c=29.4,
                        humidity_percent=48,
                        precipitation_probability=5,
                        cloud_cover=10,
                        wind_speed_kmh=9.0,
                        dew_point_c=16.1,
                        apparent_temperature_c=30.0,
                        precipitation_total=0.0,
                        precipitation_snow=0.0,
                    )
                ],
            )

        with patch(
            "app.api.weather.obtain_google_weather_forecast",
            new=fake_obtain_google_weather_forecast,
        ):
            response = client.get(
                "/api/weather/google_weather/forecast",
                params={
                    "latitude": BARCELONA_LATITUDE,
                    "longitude": BARCELONA_LONGITUDE,
                    "days": 1,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider"], "google_weather")
        self.assertGreater(len(response.json()["forecast"]), 0)

    @unittest.skipUnless(
        RUN_REAL_OPEN_METEO_TESTS,
        "Define RUN_REAL_OPEN_METEO_TESTS=1 para ejecutar la peticion real.",
    )
    def test_get_forecast_with_real_open_meteo_for_barcelona(self) -> None:
        response = client.get(
            "/api/weather/open_meteo/forecast",
            params={
                "latitude": BARCELONA_LATITUDE,
                "longitude": BARCELONA_LONGITUDE,
                "days": 1,
            },
        )

        self.assertEqual(response.status_code, 200)

        payload = response.json()

        self.assertEqual(payload["provider"], "open_meteo")
        self.assertAlmostEqual(payload["latitude"], BARCELONA_LATITUDE, delta=0.05)
        self.assertAlmostEqual(payload["longitude"], BARCELONA_LONGITUDE, delta=0.05)
        self.assertTrue(payload["timezone"])
        self.assertGreater(len(payload["forecast"]), 0)

        first_point = payload["forecast"][0]

        self.assertIsInstance(first_point["datetime"], str)
        self.assertIsInstance(first_point["temperature_c"], (int, float))
        self.assertIsInstance(first_point["humidity_percent"], (int, float))
        self.assertIsInstance(first_point["precipitation_probability"], (int, float))
        self.assertIsInstance(first_point["cloud_cover"], (int, float))
        self.assertIsInstance(first_point["wind_speed_kmh"], (int, float))
        self.assertIsInstance(first_point["dew_point_c"], (int, float))
        self.assertIsInstance(first_point["apparent_temperature_c"], (int, float))
        self.assertIsInstance(first_point["precipitation_total"], (int, float))
        self.assertIsInstance(first_point["precipitation_snow"], (int, float))


if __name__ == "__main__":
    unittest.main()
