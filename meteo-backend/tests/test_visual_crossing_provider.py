import os
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from app.core.config import get_settings
from app.models.weather import ProviderForecast
from app.providers.visual_crossing import fetch_visual_crossing
from app.services.visual_crossing_service import (
    normalize_visual_crossing,
    obtain_visual_crossing_forecast,
)


BARCELONA_LATITUDE = 41.3874
BARCELONA_LONGITUDE = 2.1686
RUN_REAL_VISUAL_CROSSING_TESTS = os.getenv(
    "RUN_REAL_VISUAL_CROSSING_TESTS"
) in {"1", "true", "TRUE"}
SETTINGS = get_settings()
HAS_VISUAL_CROSSING_CREDENTIALS = bool(SETTINGS.visual_crossing_api_key)


class _FakeResponse:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "latitude": BARCELONA_LATITUDE,
            "longitude": BARCELONA_LONGITUDE,
            "timezone": "Europe/Madrid",
            "days": [],
        }


class _FakeAsyncClient:
    def __init__(self) -> None:
        self.requests: list[tuple[str, dict]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        return None

    async def get(self, url: str, params: dict) -> _FakeResponse:
        self.requests.append((url, params))
        return _FakeResponse()


class VisualCrossingClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_visual_crossing_requests_only_used_fields(self) -> None:
        fake_client = _FakeAsyncClient()
        fake_settings = SimpleNamespace(
            visual_crossing_api_key="visual-crossing-key",
            http_timeout_seconds=10.0,
        )

        with patch(
            "app.providers.visual_crossing.get_settings",
            return_value=fake_settings,
        ), patch(
            "app.providers.visual_crossing.httpx.AsyncClient",
            return_value=fake_client,
        ):
            result = await fetch_visual_crossing(
                latitude=BARCELONA_LATITUDE,
                longitude=BARCELONA_LONGITUDE,
                days=7,
            )

        self.assertEqual(result["timezone"], "Europe/Madrid")
        self.assertEqual(len(fake_client.requests), 1)
        url, params = fake_client.requests[0]
        self.assertTrue(url.endswith("/41.3874,2.1686/next7days"))
        self.assertEqual(params["key"], "visual-crossing-key")
        self.assertEqual(params["unitGroup"], "metric")
        self.assertEqual(params["include"], "days,hours")
        self.assertEqual(params["contentType"], "json")
        self.assertEqual(
            set(params["elements"].split(",")),
            {
                "datetime",
                "datetimeEpoch",
                "timezone",
                "temp",
                "tempmin",
                "tempmax",
                "feelslike",
                "humidity",
                "precip",
                "precipprob",
                "snow",
                "cloudcover",
                "windspeed",
            },
        )


class VisualCrossingNormalizationTestCase(unittest.TestCase):
    def test_normalize_visual_crossing_keeps_metric_units_and_missing_probability(
        self,
    ) -> None:
        first_hour = datetime(2026, 7, 28, 8, tzinfo=timezone.utc)
        second_hour = datetime(2026, 7, 28, 9, tzinfo=timezone.utc)
        data = {
            "latitude": BARCELONA_LATITUDE,
            "longitude": BARCELONA_LONGITUDE,
            "timezone": "Europe/Madrid",
            "days": [
                {
                    "datetime": "2026-07-28",
                    "tempmin": 18.0,
                    "tempmax": 29.0,
                    "precip": 3.4,
                    "snow": 1.2,
                    "cloudcover": 65.0,
                    "hours": [
                        {
                            "datetime": "10:00:00",
                            "datetimeEpoch": first_hour.timestamp(),
                            "temp": 25.5,
                            "feelslike": 26.2,
                            "humidity": 55.0,
                            "precip": 1.2,
                            "snow": 0.4,
                            "cloudcover": 80.0,
                            "windspeed": 12.4,
                        },
                        {
                            "datetime": "11:00:00",
                            "datetimeEpoch": second_hour.timestamp(),
                            "temp": 26.0,
                            "feelslike": 27.0,
                            "humidity": 52.0,
                            "precip": 0.0,
                            "precipprob": 37.0,
                            "snow": 0.0,
                            "cloudcover": 30.0,
                            "windspeed": 10.0,
                        },
                    ],
                }
            ],
        }

        forecast = normalize_visual_crossing(
            data=data,
            latitude=BARCELONA_LATITUDE,
            longitude=BARCELONA_LONGITUDE,
            days=7,
        )

        self.assertEqual(forecast.provider, "visual_crossing")
        self.assertEqual(forecast.timezone, "Europe/Madrid")
        self.assertEqual(len(forecast.forecast), 2)

        first_point = forecast.forecast[0]
        second_point = forecast.forecast[1]
        self.assertEqual(first_point.datetime, first_hour)
        self.assertEqual(first_point.temperature_c, 25.5)
        self.assertEqual(first_point.apparent_temperature_c, 26.2)
        self.assertEqual(first_point.humidity_percent, 55.0)
        self.assertEqual(first_point.wind_speed_kmh, 12.4)
        self.assertEqual(first_point.precipitation_total, 1.2)
        self.assertEqual(first_point.precipitation_snow, 0.4)
        self.assertIsNone(first_point.precipitation_probability)
        self.assertEqual(second_point.precipitation_probability, 37.0)

        self.assertEqual(len(forecast.daily_forecast), 1)
        daily_point = forecast.daily_forecast[0]
        self.assertEqual(str(daily_point.date), "2026-07-28")
        self.assertEqual(daily_point.temperature_min_c, 18.0)
        self.assertEqual(daily_point.temperature_max_c, 29.0)
        self.assertEqual(daily_point.precipitation_total, 3.4)
        self.assertEqual(daily_point.precipitation_snow, 1.2)
        self.assertEqual(daily_point.cloud_cover, 65.0)


class VisualCrossingProviderIntegrationTestCase(
    unittest.IsolatedAsyncioTestCase
):
    @unittest.skipUnless(
        RUN_REAL_VISUAL_CROSSING_TESTS,
        "Define RUN_REAL_VISUAL_CROSSING_TESTS=1 para ejecutar la peticion real.",
    )
    @unittest.skipUnless(
        HAS_VISUAL_CROSSING_CREDENTIALS,
        "Define VISUAL_CROSSING_API_KEY para el test real.",
    )
    async def test_obtain_visual_crossing_returns_prediction_for_barcelona(
        self,
    ) -> None:
        forecast = await obtain_visual_crossing_forecast(
            latitude=BARCELONA_LATITUDE,
            longitude=BARCELONA_LONGITUDE,
            days=7,
        )

        self.assertIsInstance(forecast, ProviderForecast)
        self.assertEqual(forecast.provider, "visual_crossing")
        self.assertTrue(forecast.timezone)
        self.assertGreater(len(forecast.forecast), 0)
        self.assertGreater(len(forecast.daily_forecast), 0)
        self.assertLessEqual(len(forecast.daily_forecast), 7)

        first_point = forecast.forecast[0]
        self.assertIsInstance(first_point.datetime, datetime)
        self.assertIsInstance(first_point.temperature_c, float)
        if first_point.precipitation_probability is not None:
            self.assertGreaterEqual(first_point.precipitation_probability, 0.0)
            self.assertLessEqual(first_point.precipitation_probability, 100.0)


if __name__ == "__main__":
    unittest.main()
