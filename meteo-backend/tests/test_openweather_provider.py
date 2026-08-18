import os
import unittest
from datetime import datetime, timezone

from app.core.config import get_settings
from app.models.weather import ProviderForecast
from app.services.openweather_service import (
    normalize_openweather,
    obtain_openweather_forecast,
)


BARCELONA_LATITUDE = 41.3874
BARCELONA_LONGITUDE = 2.1686
RUN_REAL_OPENWEATHER_TESTS = os.getenv("RUN_REAL_OPENWEATHER_TESTS") in {
    "1",
    "true",
    "TRUE",
}
HAS_OPENWEATHER_API_KEY = bool(get_settings().openweather_api_key)


def _timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value).replace(tzinfo=timezone.utc).timestamp())


class OpenWeatherNormalizationTestCase(unittest.TestCase):
    def test_normalize_openweather_maps_three_hour_forecast(self) -> None:
        data = {
            "city": {
                "timezone": 7200,
            },
            "list": [
                {
                    "dt": _timestamp("2026-07-27T00:00:00"),
                    "main": {
                        "temp": 20.0,
                        "feels_like": 19.5,
                        "humidity": 70,
                    },
                    "clouds": {"all": 60},
                    "wind": {"speed": 2.0},
                    "pop": 0.45,
                    "rain": {"3h": 1.2},
                    "snow": {"3h": 2.0},
                },
                {
                    "dt": _timestamp("2026-07-27T03:00:00"),
                    "main": {
                        "temp": 21.0,
                        "feels_like": 20.5,
                        "humidity": 65,
                    },
                    "clouds": {"all": 20},
                    "wind": {"speed": 1.5},
                    "pop": 0.0,
                },
                {
                    "dt": _timestamp("2026-07-27T06:00:00"),
                    "main": {
                        "temp": 23.0,
                        "feels_like": 22.5,
                        "humidity": 55,
                    },
                    "clouds": {"all": 10},
                    "wind": {"speed": 1.0},
                    "rain": {"3h": 0.3},
                },
                {
                    "dt": _timestamp("2026-07-28T00:00:00"),
                    "main": {
                        "temp": 18.0,
                        "feels_like": 17.5,
                        "humidity": 75,
                    },
                    "clouds": {"all": 80},
                    "wind": {"speed": 3.0},
                    "pop": 0.2,
                },
            ],
        }

        forecast = normalize_openweather(
            data=data,
            latitude=BARCELONA_LATITUDE,
            longitude=BARCELONA_LONGITUDE,
            days=1,
        )

        self.assertEqual(forecast.provider, "openweather")
        self.assertEqual(forecast.timezone, "+02:00")
        self.assertEqual(len(forecast.forecast), 3)

        first_point = forecast.forecast[0]
        third_point = forecast.forecast[2]

        self.assertEqual(first_point.temperature_c, 20.0)
        self.assertEqual(first_point.humidity_percent, 70.0)
        self.assertIsNone(first_point.precipitation_probability)
        self.assertIsNone(first_point.precipitation_total)
        self.assertIsNone(first_point.precipitation_snow)
        self.assertEqual(first_point.wind_speed_kmh, 7.2)
        self.assertEqual(first_point.apparent_temperature_c, 19.5)
        self.assertIsNone(third_point.precipitation_probability)
        self.assertIsNone(third_point.precipitation_total)
        self.assertIsNone(third_point.precipitation_snow)


class OpenWeatherProviderIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(
        RUN_REAL_OPENWEATHER_TESTS,
        "Define RUN_REAL_OPENWEATHER_TESTS=1 para ejecutar la peticion real.",
    )
    @unittest.skipUnless(
        HAS_OPENWEATHER_API_KEY,
        "Define OPENWEATHER_API_KEY para ejecutar el test real de OpenWeather.",
    )
    async def test_obtain_openweather_forecast_returns_prediction_for_barcelona(
        self,
    ) -> None:
        forecast = await obtain_openweather_forecast(
            latitude=BARCELONA_LATITUDE,
            longitude=BARCELONA_LONGITUDE,
            days=7,
        )

        self.assertIsInstance(forecast, ProviderForecast)
        self.assertEqual(forecast.provider, "openweather")
        self.assertTrue(forecast.timezone)
        self.assertGreater(len(forecast.forecast), 0)
        self.assertLessEqual(len(forecast.forecast), 40)

        first_point = forecast.forecast[0]

        self.assertIsInstance(first_point.datetime, datetime)
        self.assertIsInstance(first_point.temperature_c, float)
        self.assertIsInstance(first_point.humidity_percent, float)
        self.assertIsNone(first_point.precipitation_probability)
        self.assertIsInstance(first_point.cloud_cover, float)
        self.assertIsInstance(first_point.wind_speed_kmh, float)
        self.assertIsNone(first_point.precipitation_total)
        self.assertIsNone(first_point.precipitation_snow)
        self.assertIsInstance(first_point.apparent_temperature_c, float)


if __name__ == "__main__":
    unittest.main()
