import os
import unittest
from datetime import datetime

from app.core.config import get_settings
from app.models.weather import ProviderForecast
from app.services.google_weather_service import obtain_google_weather_forecast


BARCELONA_LATITUDE = 41.3874
BARCELONA_LONGITUDE = 2.1686
RUN_REAL_GOOGLE_WEATHER_TESTS = os.getenv("RUN_REAL_GOOGLE_WEATHER_TESTS") in {
    "1",
    "true",
    "TRUE",
}
HAS_GOOGLE_WEATHER_API_KEY = bool(get_settings().google_weather_api_key)


class GoogleWeatherProviderIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(
        RUN_REAL_GOOGLE_WEATHER_TESTS,
        "Define RUN_REAL_GOOGLE_WEATHER_TESTS=1 para ejecutar la peticion real.",
    )
    @unittest.skipUnless(
        HAS_GOOGLE_WEATHER_API_KEY,
        "Define GOOGLE_WEATHER_API_KEY para ejecutar el test real de Google Weather.",
    )
    async def test_obtain_google_weather_forecast_returns_prediction_for_barcelona(
        self,
    ) -> None:
        forecast = await obtain_google_weather_forecast(
            latitude=BARCELONA_LATITUDE,
            longitude=BARCELONA_LONGITUDE,
            days=1,
        )

        self.assertIsInstance(forecast, ProviderForecast)
        self.assertEqual(forecast.provider, "google_weather")
        self.assertAlmostEqual(forecast.latitude, BARCELONA_LATITUDE, delta=0.05)
        self.assertAlmostEqual(
            forecast.longitude,
            BARCELONA_LONGITUDE,
            delta=0.05,
        )
        self.assertTrue(forecast.timezone)
        self.assertGreater(len(forecast.forecast), 0)

        first_point = forecast.forecast[0]

        self.assertIsInstance(first_point.datetime, datetime)
        self.assertIsInstance(first_point.temperature_c, float)
        self.assertIsInstance(first_point.humidity_percent, (int, float))
        self.assertIsInstance(first_point.precipitation_probability, (int, float))
        self.assertIsInstance(first_point.cloud_cover, (int, float))
        self.assertIsInstance(first_point.wind_speed_kmh, (int, float))
        self.assertIsInstance(first_point.dew_point_c, (int, float))
        self.assertIsInstance(first_point.apparent_temperature_c, (int, float))
        self.assertGreaterEqual(first_point.precipitation_total or 0.0, 0.0)
        self.assertGreaterEqual(first_point.precipitation_snow or 0.0, 0.0)


if __name__ == "__main__":
    unittest.main()
