from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.location import LocationSearchResponse
from app.providers.exceptions import LocationProviderError
from app.services.location_search_service import search_locations


router = APIRouter(prefix="/api/locations", tags=["locations"])


@router.get("/search", response_model=LocationSearchResponse)
async def search_location_candidates(
    q: Annotated[str, Query(min_length=2)],
    count: Annotated[int, Query(ge=1, le=20)] = 10,
    language: Annotated[str, Query(min_length=2, max_length=5)] = "es",
    country_code: Annotated[Optional[str], Query(min_length=2, max_length=2)] = None,
) -> LocationSearchResponse:
    try:
        normalized_country_code = country_code.upper() if country_code else None
        return await search_locations(
            query=q,
            count=count,
            language=language.lower(),
            country_code=normalized_country_code,
        )
    except LocationProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
