import os
import unittest
from datetime import datetime

from app.core.config import get_settings
from app.models.weather import ProviderForecast
from app.services.meteosource_service import (
    normalize_meteosource,
    obtain_meteosource_forecast,
)


BARCELONA_LATITUDE = 41.3874
BARCELONA_LONGITUDE = 2.1686
RUN_REAL_METEOSOURCE_TESTS = os.getenv("RUN_REAL_METEOSOURCE_TESTS") in {
    "1",
    "true",
    "TRUE",
}
HAS_METEOSOURCE_API_KEY = bool(get_settings().meteosource_api_key)


class MeteosourceNormalizationTestCase(unittest.TestCase):
    def test_normalize_meteosource_excludes_unsupported_precipitation_types(
        self,
    ) -> None:
        precipitation_cases = [
            ("none", 0.0, None, 0.0, None, 0.0),
            ("rain", 1.2, None, 1.2, None, 0.0),
            ("snow", 2.5, None, 2.5, None, 2.5),
            ("rain_snow", 3.0, 63, None, None, None),
            ("ice pellets", 0.8, 64, None, None, None),
            ("frozen rain", 1.1, 65, None, None, None),
            ("hail", 0.6, 66, None, None, None),
        ]
        hourly_data = []

        for index, (kind, total, probability, _, _, _) in enumerate(
            precipitation_cases
        ):
            hour = {
                "date": f"2026-07-27T{index:02d}:00:00",
                "temperature": 20.0 + index,
                "wind": {"speed": 2.0},
                "cloud_cover": {"total": 40},
                "precipitation": {
                    "total": total,
                    "type": kind,
                },
            }
            if probability is not None:
                hour["probability"] = {"precipitation": probability}
            hourly_data.append(hour)

        hourly_data.append(
            {
                "date": "2026-07-27T07:00:00",
                "temperature": 27.0,
                "probability": {"precipitation": 37},
                "wind": {"speed": 1.0},
                "cloud_cover": {"total": 20},
                "precipitation": {
                    "total": 0.4,
                    "type": "rain",
                },
            }
        )
        data = {
            "timezone": "Europe/Madrid",
            "hourly": {"data": hourly_data},
            "daily": {
                "data": [
                    {
                        "day": "2026-07-27",
                        "all_day": {
                            "temperature_min": 18.0,
                            "temperature_max": 27.0,
                            "cloud_cover": {"total": 65},
                            "precipitation": {
                                "total": 2.0,
                                "type": "snow",
                            },
                        },
                    },
                    {
                        "day": "2026-07-28",
                        "all_day": {
                            "temperature_min": 19.0,
                            "temperature_max": 28.0,
                            "cloud_cover": {"total": 70},
                            "precipitation": {
                                "total": 4.0,
                                "type": "ice pellets",
                            },
                        },
                    }
                ]
            },
        }

        forecast = normalize_meteosource(
            data=data,
            latitude=BARCELONA_LATITUDE,
            longitude=BARCELONA_LONGITUDE,
            days=2,
        )

        self.assertEqual(forecast.provider, "meteosource")
        self.assertEqual(forecast.timezone, "Europe/Madrid")
        self.assertEqual(len(forecast.forecast), 8)

        for point, (_, _, _, total, probability, snow) in zip(
            forecast.forecast,
            precipitation_cases,
        ):
            self.assertEqual(point.precipitation_total, total)
            self.assertIs(point.precipitation_probability, probability)
            self.assertEqual(point.precipitation_snow, snow)
            self.assertEqual(point.wind_speed_kmh, 7.2)

        self.assertEqual(forecast.forecast[-1].precipitation_probability, 37.0)
        self.assertEqual(len(forecast.daily_forecast), 2)
        self.assertEqual(forecast.daily_forecast[0].precipitation_total, 2.0)
        self.assertEqual(forecast.daily_forecast[0].precipitation_snow, 2.0)
        self.assertIsNone(forecast.daily_forecast[1].precipitation_total)
        self.assertIsNone(forecast.daily_forecast[1].precipitation_snow)


class MeteosourceProviderIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(
        RUN_REAL_METEOSOURCE_TESTS,
        "Define RUN_REAL_METEOSOURCE_TESTS=1 para ejecutar la peticion real.",
    )
    @unittest.skipUnless(
        HAS_METEOSOURCE_API_KEY,
        "Define METEOSOURCE_API_KEY para ejecutar el test real de Meteosource.",
    )
    async def test_obtain_meteosource_forecast_returns_prediction_for_barcelona(
        self,
    ) -> None:
        forecast = await obtain_meteosource_forecast(
            latitude=BARCELONA_LATITUDE,
            longitude=BARCELONA_LONGITUDE,
            days=7,
        )

        self.assertIsInstance(forecast, ProviderForecast)
        self.assertEqual(forecast.provider, "meteosource")
        self.assertEqual(forecast.timezone, "Europe/Madrid")
        self.assertEqual(len(forecast.forecast), 24)
        self.assertEqual(len(forecast.daily_forecast), 7)

        first_point = forecast.forecast[0]

        self.assertIsInstance(first_point.datetime, datetime)
        self.assertIsInstance(first_point.temperature_c, float)
        self.assertTrue(
            first_point.precipitation_probability is None
            or isinstance(first_point.precipitation_probability, float)
        )
        self.assertIsInstance(first_point.cloud_cover, float)
        self.assertIsInstance(first_point.wind_speed_kmh, float)
        self.assertIsInstance(first_point.precipitation_total, float)
        self.assertTrue(
            first_point.precipitation_snow is None
            or isinstance(first_point.precipitation_snow, float)
        )


if __name__ == "__main__":
    unittest.main()
