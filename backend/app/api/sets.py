"""Endpoints backing the catalogue's filter controls."""

from typing import Annotated

from fastapi import APIRouter, Depends

from ..dependencies import get_catalogue_service
from ..schemas.catalogue import CardSetSummary, FilterOptions
from ..services.catalogue import CatalogueService

router = APIRouter(tags=["catalogue"])


@router.get(
    "/sets",
    response_model=list[CardSetSummary],
    summary="Every card set, newest release first",
)
def card_sets(
    service: Annotated[CatalogueService, Depends(get_catalogue_service)],
) -> list[CardSetSummary]:
    """All sets, including ones with nothing in stock.

    A shopper who filters by a set and sees nothing has learned that none are for
    sale, which beats the set being silently missing from the list.
    """
    return service.card_sets()


@router.get(
    "/filter-options",
    response_model=FilterOptions,
    summary="Distinct rarities, variants and conditions currently for sale",
)
def filter_options(
    service: Annotated[CatalogueService, Depends(get_catalogue_service)],
) -> FilterOptions:
    return service.filter_options()
