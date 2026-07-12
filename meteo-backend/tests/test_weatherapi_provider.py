import os
import unittest
from datetime import datetime

from app.core.config import get_settings
from app.models.weather import ProviderForecast
from app.services.weather_api import obtain_weather_api_forecast


BARCELONA_LATITUDE = 41.3874
BARCELONA_LONGITUDE = 2.1686
RUN_REAL_WEATHER_API_TESTS = os.getenv("RUN_REAL_WEATHER_API_TESTS") in {
    "1",
    "true",
    "TRUE",
}
HAS_WEATHER_API_KEY = bool(get_settings().weather_api_key)


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

        first_point = forecast.forecast[0]

        self.assertIsInstance(first_point.datetime, datetime)
        self.assertIsInstance(first_point.temperature_c, float)
        self.assertIsInstance(first_point.humidity_percent, float)
        self.assertIsInstance(first_point.precipitation_probability, float)
        self.assertIsInstance(first_point.cloud_cover, float)
        self.assertIsInstance(first_point.wind_speed_kmh, float)
        self.assertIsInstance(first_point.dew_point_c, float)
        self.assertIsInstance(first_point.precipitation_total, float)
        self.assertIsInstance(first_point.precipitation_snow, float)
        self.assertIsInstance(first_point.apparent_temperature_c, float)


if __name__ == "__main__":
    unittest.main()
