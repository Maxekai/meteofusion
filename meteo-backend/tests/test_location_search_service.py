import unittest

from app.services.location_search_service import normalize_open_meteo_locations


class LocationSearchServiceTestCase(unittest.TestCase):
    def test_normalize_open_meteo_locations_returns_candidates_with_display_name(
        self,
    ) -> None:
        response = normalize_open_meteo_locations(
            query="Barcelona",
            count=3,
            data={
                "results": [
                    {
                        "id": 3128760,
                        "name": "Barcelona",
                        "latitude": 41.38879,
                        "longitude": 2.15899,
                        "timezone": "Europe/Madrid",
                        "country": "España",
                        "country_code": "ES",
                        "admin1": "Catalunya",
                        "admin2": "Barcelona",
                        "elevation": 47.0,
                        "population": 1621537,
                    },
                    {
                        "id": 3648522,
                        "name": "Barcelona",
                        "latitude": 10.13333,
                        "longitude": -64.7,
                        "timezone": "America/Caracas",
                        "country": "Venezuela",
                        "country_code": "VE",
                        "admin1": "Anzoátegui",
                    },
                ]
            },
        )

        self.assertEqual(response.query, "Barcelona")
        self.assertEqual(response.count, 3)
        self.assertEqual(len(response.results), 2)

        first_result = response.results[0]
        second_result = response.results[1]

        self.assertEqual(first_result.id, "open_meteo:3128760")
        self.assertEqual(first_result.provider, "open_meteo_geocoding")
        self.assertEqual(first_result.display_name, "Barcelona, Catalunya, España")
        self.assertEqual(first_result.timezone, "Europe/Madrid")

        self.assertEqual(second_result.id, "open_meteo:3648522")
        self.assertEqual(second_result.display_name, "Barcelona, Anzoátegui, Venezuela")
        self.assertEqual(second_result.timezone, "America/Caracas")


if __name__ == "__main__":
    unittest.main()
