import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.location import LocationCandidate, LocationSearchResponse


client = TestClient(app)


class LocationsApiTestCase(unittest.TestCase):
    def test_RF2(self) -> None:
        with patch("app.api.locations.search_locations") as search_mock:
            for query in ("", "B"):
                with self.subTest(query=query):
                    response = client.get(
                        "/api/locations/search",
                        params={"q": query},
                    )

                    self.assertEqual(response.status_code, 422)
                    self.assertTrue(
                        any(
                            error["loc"] == ["query", "q"]
                            for error in response.json()["detail"]
                        )
                    )

            search_mock.assert_not_called()

    def test_search_location_candidates_returns_options_for_frontend_selection(
        self,
    ) -> None:
        async def fake_search_locations(
            query: str,
            count: int,
            language: str,
            country_code: str | None,
        ) -> LocationSearchResponse:
            self.assertEqual(query, "Barcelona")
            self.assertEqual(count, 5)
            self.assertEqual(language, "es")
            self.assertEqual(country_code, "ES")
            return LocationSearchResponse(
                query=query,
                count=count,
                results=[
                    LocationCandidate(
                        id="open_meteo:3128760",
                        provider="open_meteo_geocoding",
                        provider_id=3128760,
                        name="Barcelona",
                        display_name="Barcelona, Catalunya, España",
                        latitude=41.38879,
                        longitude=2.15899,
                        timezone="Europe/Madrid",
                        country="España",
                        country_code="ES",
                        admin1="Catalunya",
                        admin2="Barcelona",
                    ),
                    LocationCandidate(
                        id="open_meteo:3648522",
                        provider="open_meteo_geocoding",
                        provider_id=3648522,
                        name="Barcelona",
                        display_name="Barcelona, Anzoátegui, Venezuela",
                        latitude=10.13333,
                        longitude=-64.7,
                        timezone="America/Caracas",
                        country="Venezuela",
                        country_code="VE",
                        admin1="Anzoátegui",
                    ),
                ],
            )

        with patch(
            "app.api.locations.search_locations",
            new=fake_search_locations,
        ):
            response = client.get(
                "/api/locations/search",
                params={
                    "q": "Barcelona",
                    "count": 5,
                    "language": "es",
                    "country_code": "es",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertEqual(payload["query"], "Barcelona")
        self.assertEqual(payload["count"], 5)
        self.assertEqual(len(payload["results"]), 2)
        self.assertEqual(
            payload["results"][0]["display_name"],
            "Barcelona, Catalunya, España",
        )
        self.assertEqual(payload["results"][0]["timezone"], "Europe/Madrid")
        self.assertEqual(payload["results"][1]["display_name"], "Barcelona, Anzoátegui, Venezuela")
        self.assertEqual(payload["results"][1]["timezone"], "America/Caracas")


if __name__ == "__main__":
    unittest.main()
