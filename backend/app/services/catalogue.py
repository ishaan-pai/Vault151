"""Catalogue business logic: paging arithmetic, and database rows to response models.

This is the only layer that knows both shapes, which is what lets the SQL keep the
view's column names while the API exposes a cleaner contract.
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from ..errors import NotFoundError
from ..repositories.catalogue import CatalogueRepository, ListingFilters, Row, SortKey
from ..schemas.catalogue import (
    CardSetSummary,
    FilterOptions,
    GradingInfo,
    ListingDetail,
    ListingPage,
    ListingSummary,
)

logger = logging.getLogger(__name__)

CURRENCY = "CAD"


def _money(value: Decimal | float | int | None) -> str:
    """Always two decimal places, as a string, so no float rounding reaches the client."""
    return f"{Decimal(str(value or 0)):.2f}"


def _as_date(value: datetime | date | None) -> date:
    """Oracle DATE arrives as a datetime; the catalogue only ever shows the day."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise ValueError(f"expected a date, got {value!r}")


def _grading(row: Row) -> GradingInfo | None:
    """Grading is LEFT JOINed in the view, so these are NULL for raw cards."""
    if not row.get("grade"):
        return None
    return GradingInfo(
        company=row["gradingcompany"],
        grade=row["grade"],
        certification_number=row["certificationnumber"],
    )


def _summary_fields(row: Row) -> dict[str, Any]:
    return {
        "listing_id": int(row["listingid"]),
        "card_name": row["cardname"],
        "set_name": row["setname"],
        "collector_number": row["collectornumber"],
        "variant": row["variant"],
        "rarity": row["rarity"],
        "card_condition": row["cardcondition"],
        "asking_price": _money(row["asking_price_cad"]),
        "currency": CURRENCY,
        "image_url": row.get("imageurl"),
        "listed_at": _as_date(row["listedat"]),
        "grading": _grading(row),
    }


def to_summary(row: Row) -> ListingSummary:
    return ListingSummary(**_summary_fields(row))


def to_detail(row: Row) -> ListingDetail:
    return ListingDetail(
        **_summary_fields(row),
        copy_id=int(row["copyid"]),
        set_id=int(row["setid"]),
        card_language=row["cardlanguage"],
        description=row["description"],
    )


class CatalogueService:
    def __init__(self, repository: CatalogueRepository) -> None:
        self._repository = repository

    def search(
        self,
        filters: ListingFilters,
        *,
        sort: SortKey,
        page: int,
        page_size: int,
    ) -> ListingPage:
        rows, total = self._repository.search(
            filters,
            sort=sort,
            offset=(page - 1) * page_size,
            limit=page_size,
        )
        # Ceiling division: 11 items at 12 per page is 1 page, 13 is 2.
        total_pages = -(-total // page_size) if page_size else 0
        return ListingPage(
            items=[to_summary(row) for row in rows],
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
        )

    def get(self, listing_id: int) -> ListingDetail:
        row = self._repository.get(listing_id)
        if row is None:
            # Covers both "never existed" and "no longer for sale": the catalogue
            # view only contains Active listings, and the distinction is not the
            # buyer's business.
            raise NotFoundError(f"No listing {listing_id} is currently for sale.")
        return to_detail(row)

    def featured(self, limit: int) -> list[ListingSummary]:
        return [to_summary(row) for row in self._repository.featured(limit)]

    def card_sets(self) -> list[CardSetSummary]:
        return [
            CardSetSummary(
                set_id=int(row["setid"]),
                set_name=row["setname"],
                release_date=_as_date(row["releasedate"]),
            )
            for row in self._repository.card_sets()
        ]

    def filter_options(self) -> FilterOptions:
        """Fold the (kind, value) pairs into one list per filter."""
        grouped: dict[str, list[str]] = {"rarity": [], "variant": [], "condition": []}
        for row in self._repository.filter_options():
            kind = str(row["option_kind"])
            if kind in grouped:
                grouped[kind].append(str(row["option_value"]))
        return FilterOptions(
            rarities=grouped["rarity"],
            variants=grouped["variant"],
            conditions=grouped["condition"],
        )
