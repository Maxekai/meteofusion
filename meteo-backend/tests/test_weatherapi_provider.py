import os
import unittest
from datetime import datetime

from app.core.config import get_settings
from app.models.weather import ProviderForecast
from app.services.weather_api import normalize_weather_api, obtain_weather_api_forecast


BARCELONA_LATITUDE = 41.3874
BARCELONA_LONGITUDE = 2.1686
RUN_REAL_WEATHER_API_TESTS = os.getenv("RUN_REAL_WEATHER_API_TESTS") in {
    "1",
    "true",
    "TRUE",
}
HAS_WEATHER_API_KEY = bool(get_settings().weather_api_key)


class WeatherApiNormalizationTestCase(unittest.TestCase):
    def test_normalize_weather_api_uses_native_daily_extremes(self) -> None:
        forecast = normalize_weather_api(
            {
                "location": {
                    "lat": BARCELONA_LATITUDE,
                    "lon": BARCELONA_LONGITUDE,
                    "tz_id": "Europe/Madrid",
                },
                "forecast": {
                    "forecastday": [
                        {
                            "date": "2026-08-03",
                            "day": {
                                "mintemp_c": 20.0,
                                "maxtemp_c": 30.0,
                                "totalprecip_mm": 2.4,
                                "totalsnow_cm": 0.0,
                            },
                            "hour": [
                                {
                                    "time": "2026-08-03 00:00",
                                    "temp_c": 22.0,
                                    "cloud": 20,
                                },
                                {
                                    "time": "2026-08-03 01:00",
                                    "temp_c": 21.0,
                                    "cloud": 60,
                                },
                            ],
                        }
                    ]
                },
            }
        )

        self.assertEqual(len(forecast.daily_forecast), 1)
        daily_point = forecast.daily_forecast[0]
        self.assertEqual(str(daily_point.date), "2026-08-03")
        self.assertEqual(daily_point.temperature_min_c, 20.0)
        self.assertEqual(daily_point.temperature_max_c, 30.0)
        self.assertEqual(daily_point.precipitation_total, 2.4)
        self.assertEqual(daily_point.precipitation_snow, 0.0)
        self.assertEqual(daily_point.cloud_cover, 40.0)


class WeatherApiProviderIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(
        RUN_REAL_WEATHER_API_TESTS,
        "Define RUN_REAL_WEATHER_API_TESTS=1 para ejecutar la peticion real.",
    )
    @unittest.skipUnless(
        HAS_WEATHER_API_KEY,
        "Define WEATHER_API_KEY para ejecutar el test real de WeatherAPI.",
    )
    async def test_obtain_weather_api_forecast_returns_prediction_for_barcelona(
        self,
    ) -> None:
        forecast = await obtain_weather_api_forecast(
            latitude=BARCELONA_LATITUDE,
            longitude=BARCELONA_LONGITUDE,
            days=1,
        )

        self.assertIsInstance(forecast, ProviderForecast)
        self.assertEqual(forecast.provider, "weather_api")
        self.assertAlmostEqual(forecast.latitude, BARCELONA_LATITUDE, delta=0.05)
        self.assertAlmostEqual(
            forecast.longitude,
            BARCELONA_LONGITUDE,
            delta=0.05,
        )
        self.assertEqual(forecast.timezone, "Europe/Madrid")
        self.assertGreater(len(forecast.forecast), 0)
        self.assertGreater(len(forecast.daily_forecast), 0)

        first_point = forecast.forecast[0]

        self.assertIsInstance(first_point.datetime, datetime)
        self.assertIsInstance(first_point.temperature_c, float)
        self.assertIsInstance(first_point.humidity_percent, float)
        self.assertIsInstance(first_point.precipitation_probability, float)
        self.assertIsInstance(first_point.cloud_cover, float)
        self.assertIsInstance(first_point.wind_speed_kmh, float)
        self.assertIsInstance(first_point.precipitation_total, float)
        self.assertIsInstance(first_point.precipitation_snow, float)
        self.assertIsInstance(first_point.apparent_temperature_c, float)


if __name__ == "__main__":
    unittest.main()
