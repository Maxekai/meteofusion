import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from app.models.weather import ForecastPoint, ProviderForecast


client = TestClient(app)
BARCELONA_LATITUDE = 41.3874
BARCELONA_LONGITUDE = 2.1686
RUN_REAL_OPEN_METEO_TESTS = os.getenv("RUN_REAL_OPEN_METEO_TESTS") in {
    "1",
    "true",
    "TRUE",
}


class WeatherApiTestCase(unittest.TestCase):
    def test_get_forecast_returns_normalized_payload(self) -> None:
        async def fake_obtain_weather_forecast(
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
                        wind_speed_kmh=14.2,
                        dew_point_c=18.4,
                        apparent_temperature_c=30.1,
                        precipitation_total=1.2,
                        precipitation_snow=0.0,
                    )
                ],
            )

        with patch(
            "app.api.weather.obtain_weather_forecast",
            new=fake_obtain_weather_forecast,
        ):
            response = client.get(
                "/api/weather/forecast",
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
                        "wind_speed_kmh": 14.2,
                        "dew_point_c": 18.4,
                        "apparent_temperature_c": 30.1,
                        "precipitation_total": 1.2,
                        "precipitation_snow": 0.0,
                    }
                ],
            },
        )

    @unittest.skipUnless(
        RUN_REAL_OPEN_METEO_TESTS,
        "Define RUN_REAL_OPEN_METEO_TESTS=1 para ejecutar la peticion real.",
    )
    def test_get_forecast_with_real_open_meteo_for_barcelona(self) -> None:
        response = client.get(
            "/api/weather/forecast",
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
        self.assertIsInstance(first_point["wind_speed_kmh"], (int, float))
        self.assertIsInstance(first_point["dew_point_c"], (int, float))
        self.assertIsInstance(first_point["apparent_temperature_c"], (int, float))
        self.assertIsInstance(first_point["precipitation_total"], (int, float))
        self.assertIsInstance(first_point["precipitation_snow"], (int, float))


if __name__ == "__main__":
    unittest.main()
