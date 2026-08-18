import unittest

from app.services.open_meteo_service import normalize_open_meteo


class OpenMeteoNormalizationTestCase(unittest.TestCase):
    def test_normalize_open_meteo_uses_native_daily_extremes(self) -> None:
        forecast = normalize_open_meteo(
            {
                "latitude": 41.3874,
                "longitude": 2.1686,
                "timezone": "Europe/Madrid",
                "hourly": {
                    "time": [
                        "2026-08-03T00:00",
                        "2026-08-03T01:00",
                    ],
                    "temperature_2m": [22.0, 21.0],
                    "relative_humidity_2m": [70, 74],
                    "precipitation_probability": [10, 20],
                    "cloud_cover": [20, 60],
                    "wind_speed_10m": [8.0, 7.0],
                    "precipitation": [0.0, 0.2],
                    "snowfall": [0.0, 0.0],
                    "apparent_temperature": [23.0, 22.0],
                },
                "daily": {
                    "time": ["2026-08-03"],
                    "temperature_2m_min": [19.0],
                    "temperature_2m_max": [32.0],
                    "precipitation_sum": [1.8],
                    "snowfall_sum": [0.0],
                },
            }
        )

        self.assertEqual(len(forecast.daily_forecast), 1)
        daily_point = forecast.daily_forecast[0]
        self.assertEqual(str(daily_point.date), "2026-08-03")
        self.assertEqual(daily_point.temperature_min_c, 19.0)
        self.assertEqual(daily_point.temperature_max_c, 32.0)
        self.assertEqual(daily_point.precipitation_total, 1.8)
        self.assertEqual(daily_point.precipitation_snow, 0.0)
        self.assertEqual(daily_point.cloud_cover, 40.0)


if __name__ == "__main__":
    unittest.main()
