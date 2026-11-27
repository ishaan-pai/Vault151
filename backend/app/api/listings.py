"""Catalogue endpoints.

Query parameters are validated here, once, by FastAPI and Pydantic; the service and
repository below trust what they are given. Endpoints are sync ``def`` so the blocking
Oracle driver runs in FastAPI's threadpool.
"""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from ..config import Settings
from ..dependencies import get_catalogue_service, get_settings_dependency
from ..repositories.catalogue import DEFAULT_SORT, ListingFilters, SortKey
from ..schemas.catalogue import ListingDetail, ListingPage, ListingSummary
from ..services.catalogue import CatalogueService

router = APIRouter(tags=["catalogue"])


@router.get(
    "/listings/featured",
    response_model=list[ListingSummary],
    summary="The most valuable cards currently for sale",
)
def featured_listings(
    service: Annotated[CatalogueService, Depends(get_catalogue_service)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> list[ListingSummary]:
    """Declared before /listings/{listing_id} so "featured" is not read as an id."""
    return service.featured(settings.featured_count)


@router.get(
    "/listings",
    response_model=ListingPage,
    summary="Search the catalogue",
)
def search_listings(
    service: Annotated[CatalogueService, Depends(get_catalogue_service)],
    settings: Annotated[Settings, Depends(get_settings_dependency)],
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    page_size: Annotated[int | None, Query(alias="pageSize", ge=1, le=48)] = None,
    sort: Annotated[SortKey, Query()] = DEFAULT_SORT,
    set_id: Annotated[int | None, Query(alias="setId", ge=1)] = None,
    rarity: Annotated[str | None, Query(max_length=40)] = None,
    variant: Annotated[str | None, Query(max_length=60)] = None,
    card_condition: Annotated[str | None, Query(alias="cardCondition", max_length=20)] = None,
    graded: Annotated[bool | None, Query(description="true, false, or omit for both")] = None,
    min_price: Annotated[Decimal | None, Query(alias="minPrice", ge=0)] = None,
    max_price: Annotated[Decimal | None, Query(alias="maxPrice", ge=0)] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
) -> ListingPage:
    """A page of active listings. Every filter is optional and combines with the rest.

    Multi-word parameters are camelCase on the wire (``pageSize``, ``setId``,
    ``minPrice``) to match the response bodies, so the whole contract reads one way.
    """
    return service.search(
        ListingFilters(
            set_id=set_id,
            rarity=rarity,
            variant=variant,
            card_condition=card_condition,
            graded=graded,
            min_price=min_price,
            max_price=max_price,
            q=q,
        ),
        sort=sort,
        page=page,
        page_size=page_size or settings.default_page_size,
    )


@router.get(
    "/listings/{listing_id}",
    response_model=ListingDetail,
    summary="One card's detail",
    responses={404: {"description": "No such listing, or it is no longer for sale."}},
)
def get_listing(
    service: Annotated[CatalogueService, Depends(get_catalogue_service)],
    listing_id: Annotated[int, Path(ge=1)],
) -> ListingDetail:
    return service.get(listing_id)
