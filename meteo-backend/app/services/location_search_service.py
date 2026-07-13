from typing import Any, Optional

from app.models.location import LocationCandidate, LocationSearchResponse
from app.providers.open_meteo_geocoding import fetch_open_meteo_locations


def _build_display_name(location: dict[str, Any]) -> str:
    parts: list[str] = []

    for key in ("name", "admin1", "country"):
        value = location.get(key)
        if not value:
            continue
        normalized_value = str(value).strip()
        if normalized_value and normalized_value not in parts:
            parts.append(normalized_value)

    return ", ".join(parts)


def normalize_open_meteo_locations(
    query: str,
    data: dict[str, Any],
    count: int,
) -> LocationSearchResponse:
    results = data.get("results", [])
    candidates: list[LocationCandidate] = []

    for location in results:
        provider_id = int(location["id"])
        candidates.append(
            LocationCandidate(
                id=f"open_meteo:{provider_id}",
                provider="open_meteo_geocoding",
                provider_id=provider_id,
                name=location["name"],
                display_name=_build_display_name(location),
                latitude=location["latitude"],
                longitude=location["longitude"],
                timezone=location["timezone"],
                country=location.get("country"),
                country_code=location.get("country_code"),
                admin1=location.get("admin1"),
                admin2=location.get("admin2"),
                admin3=location.get("admin3"),
                admin4=location.get("admin4"),
                elevation=location.get("elevation"),
                population=location.get("population"),
            )
        )

    return LocationSearchResponse(
        query=query,
        count=count,
        results=candidates,
    )


async def search_locations(
    query: str,
    count: int = 10,
    language: str = "es",
    country_code: Optional[str] = None,
) -> LocationSearchResponse:
    raw_data = await fetch_open_meteo_locations(
        query=query,
        count=count,
        language=language,
        country_code=country_code,
    )

    return normalize_open_meteo_locations(
        query=query,
        data=raw_data,
        count=count,
    )
