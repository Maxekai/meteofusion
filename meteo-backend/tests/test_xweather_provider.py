import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from app.core.config import get_settings
from app.models.weather import ProviderForecast
from app.providers.xweather import (
    XWEATHER_HOURLY_PERIOD_LIMIT,
    fetch_xweather,
)
from app.services.xweather_service import (
    normalize_xweather,
    obtain_xweather_forecast,
)


BARCELONA_LATITUDE = 41.3874
BARCELONA_LONGITUDE = 2.1686
RUN_REAL_XWEATHER_TESTS = os.getenv("RUN_REAL_XWEATHER_TESTS") in {
    "1",
    "true",
    "TRUE",
}
SETTINGS = get_settings()
HAS_XWEATHER_CREDENTIALS = bool(
    SETTINGS.xweather_client_id and SETTINGS.xweather_client_secret
)


class _FakeResponse:
    def __init__(self, interval: str) -> None:
        self.status_code = 200
        self._payload = {
            "success": True,
            "error": None,
            "response": [
                {
                    "interval": interval,
                    "profile": {"tz": "Europe/Madrid"},
                    "periods": [],
                }
            ],
        }

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class _FakeAsyncClient:
    def __init__(self) -> None:
        self.requests: list[tuple[str, dict]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        return None

    async def get(self, url: str, params: dict) -> _FakeResponse:
        self.requests.append((url, params))
        return _FakeResponse(str(params["filter"]))


class XweatherClientTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_xweather_uses_forecasts_hourly_and_daily(self) -> None:
        fake_client = _FakeAsyncClient()
        fake_settings = SimpleNamespace(
            xweather_client_id="client-id",
            xweather_client_secret="client-secret",
            http_timeout_seconds=10.0,
        )

        with patch(
            "app.providers.xweather.get_settings",
            return_value=fake_settings,
        ), patch(
            "app.providers.xweather.httpx.AsyncClient",
            return_value=fake_client,
        ):
            result = await fetch_xweather(
                latitude=BARCELONA_LATITUDE,
                longitude=BARCELONA_LONGITUDE,
                days=7,
            )

        self.assertEqual(set(result), {"hourly", "daily"})
        self.assertEqual(len(fake_client.requests), 2)

        requests_by_filter = {
            params["filter"]: (url, params)
            for url, params in fake_client.requests
        }
        hourly_url, hourly_params = requests_by_filter["1hr"]
        daily_url, daily_params = requests_by_filter["day"]

        self.assertIn("/forecasts/", hourly_url)
        self.assertNotIn("/conditions/", hourly_url)
        self.assertEqual(hourly_url, daily_url)
        self.assertEqual(
            hourly_params["limit"],
            XWEATHER_HOURLY_PERIOD_LIMIT,
        )
        self.assertEqual(daily_params["limit"], 7)
        self.assertEqual(hourly_params["client_id"], "client-id")
        self.assertEqual(hourly_params["client_secret"], "client-secret")
        self.assertEqual(
            set(hourly_params["fields"].split(",")),
            {
                "periods.dateTimeISO",
                "periods.tempC",
                "periods.feelslikeC",
                "periods.humidity",
                "periods.pop",
                "periods.precipMM",
                "periods.snowCM",
                "periods.sky",
                "periods.windSpeedKPH",
                "profile.tz",
            },
        )
        self.assertEqual(
            set(daily_params["fields"].split(",")),
            {
                "periods.dateTimeISO",
                "periods.minTempC",
                "periods.maxTempC",
                "periods.precipMM",
                "periods.snowCM",
                "periods.sky",
                "profile.tz",
            },
        )


class XweatherNormalizationTestCase(unittest.TestCase):
    def test_normalize_xweather_keeps_missing_probability_as_none(self) -> None:
        data = {
            "hourly": {
                "success": True,
                "response": [
                    {
                        "profile": {"tz": "Europe/Madrid"},
                        "periods": [
                            {
                                "dateTimeISO": "2026-07-28T10:00:00+02:00",
                                "tempC": 25.5,
                                "feelslikeC": 26.2,
                                "humidity": 55,
                                "windSpeedKPH": 12.4,
                                "precipMM": 0.0,
                                "snowCM": 0.0,
                                "sky": 15,
                            },
                            {
                                "dateTimeISO": "2026-07-28T11:00:00+02:00",
                                "minTempC": 22.0,
                                "maxTempC": 24.0,
                                "minFeelslikeC": 21.0,
                                "maxFeelslikeC": 25.0,
                                "humidity": 65,
                                "windSpeedMaxKPH": 14.0,
                                "precipMM": 1.2,
                                "snowCM": 0.0,
                                "sky": 80,
                            },
                            {
                                "dateTimeISO": "2026-07-28T12:00:00+02:00",
                                "tempC": 1.0,
                                "feelslikeC": -1.0,
                                "humidity": 90,
                                "windSpeedKPH": 8.0,
                                "precipMM": None,
                                "snowCM": 2.5,
                                "sky": 100,
                            },
                            {
                                "dateTimeISO": "2026-07-28T13:00:00+02:00",
                                "tempC": 23.0,
                                "feelslikeC": 23.0,
                                "humidity": 70,
                                "windSpeedKPH": 10.0,
                                "precipMM": 0.4,
                                "snowCM": 0.0,
                                "pop": 37,
                                "sky": 70,
                            },
                        ],
                    }
                ],
            },
            "daily": {
                "success": True,
                "response": [
                    {
                        "profile": {"tz": "Europe/Madrid"},
                        "periods": [
                            {
                                "dateTimeISO": "2026-07-28T07:00:00+02:00",
                                "minTempC": 18.0,
                                "maxTempC": 29.0,
                                "precipMM": 2.3,
                                "snowCM": 0.0,
                                "sky": 65,
                            }
                        ],
                    }
                ],
            },
        }

        forecast = normalize_xweather(
            data=data,
            latitude=BARCELONA_LATITUDE,
            longitude=BARCELONA_LONGITUDE,
            days=7,
        )

        self.assertEqual(forecast.provider, "xweather")
        self.assertEqual(forecast.timezone, "Europe/Madrid")
        self.assertEqual(len(forecast.forecast), 4)

        first_point = forecast.forecast[0]
        alternate_only_point = forecast.forecast[1]
        snow_point = forecast.forecast[2]
        probability_point = forecast.forecast[3]

        self.assertEqual(first_point.temperature_c, 25.5)
        self.assertEqual(first_point.apparent_temperature_c, 26.2)
        self.assertEqual(first_point.humidity_percent, 55.0)
        self.assertEqual(first_point.wind_speed_kmh, 12.4)
        self.assertEqual(first_point.cloud_cover, 15.0)
        self.assertIsNone(first_point.precipitation_probability)
        self.assertIsNone(alternate_only_point.temperature_c)
        self.assertIsNone(alternate_only_point.apparent_temperature_c)
        self.assertIsNone(alternate_only_point.wind_speed_kmh)
        self.assertIsNone(alternate_only_point.precipitation_probability)
        self.assertEqual(alternate_only_point.precipitation_total, 1.2)
        self.assertIsNone(snow_point.precipitation_probability)
        self.assertEqual(snow_point.precipitation_snow, 2.5)
        self.assertEqual(probability_point.precipitation_probability, 37.0)

        self.assertEqual(len(forecast.daily_forecast), 1)
        daily_point = forecast.daily_forecast[0]
        self.assertEqual(str(daily_point.date), "2026-07-28")
        self.assertEqual(daily_point.temperature_min_c, 18.0)
        self.assertEqual(daily_point.temperature_max_c, 29.0)
        self.assertEqual(daily_point.precipitation_total, 2.3)
        self.assertEqual(daily_point.precipitation_snow, 0.0)


class XweatherProviderIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(
        RUN_REAL_XWEATHER_TESTS,
        "Define RUN_REAL_XWEATHER_TESTS=1 para ejecutar la peticion real.",
    )
    @unittest.skipUnless(
        HAS_XWEATHER_CREDENTIALS,
        "Define XWEATHER_CLIENT_ID y XWEATHER_CLIENT_SECRET para el test real.",
    )
    async def test_obtain_xweather_forecast_returns_prediction_for_barcelona(
        self,
    ) -> None:
        forecast = await obtain_xweather_forecast(
            latitude=BARCELONA_LATITUDE,
            longitude=BARCELONA_LONGITUDE,
            days=7,
        )

        self.assertIsInstance(forecast, ProviderForecast)
        self.assertEqual(forecast.provider, "xweather")
        self.assertTrue(forecast.timezone)
        self.assertGreater(len(forecast.forecast), 0)
        self.assertLessEqual(
            len(forecast.forecast),
            XWEATHER_HOURLY_PERIOD_LIMIT,
        )
        self.assertGreater(len(forecast.daily_forecast), 0)
        self.assertLessEqual(len(forecast.daily_forecast), 7)

        first_point = forecast.forecast[0]

        self.assertIsInstance(first_point.datetime, datetime)
        self.assertIsInstance(first_point.temperature_c, float)
        self.assertIsInstance(first_point.precipitation_probability, float)
        self.assertGreaterEqual(first_point.precipitation_probability, 0.0)
        self.assertLessEqual(first_point.precipitation_probability, 100.0)


if __name__ == "__main__":
    unittest.main()
