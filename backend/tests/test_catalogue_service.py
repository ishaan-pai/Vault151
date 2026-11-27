"""Unit tests for the catalogue service: row mapping and paging arithmetic.

A faked repository stands in for the database, so these assert the translation from
view columns to the API contract - the layer most likely to carry a silent typo.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pytest

from app.errors import NotFoundError
from app.repositories.catalogue import ListingFilters, Row, SortKey
from app.services.catalogue import CatalogueService

RAW_ROW: Row = {
    "listingid": 100,
    "copyid": 100,
    "setid": 100,
    "cardname": "Rayquaza V",
    "setname": "Evolving Skies",
    "collectornumber": "194/203",
    "cardlanguage": "English",
    "variant": "Alternate Full Art",
    "rarity": "Ultra Rare",
    "cardcondition": "NearMint",
    "description": "Raw, Near Mint.",
    "asking_price_cad": Decimal("663.00"),
    "imageurl": None,
    "listedat": datetime(2026, 11, 26, 0, 0),
    "gradingcompany": None,
    "grade": None,
    "certificationnumber": None,
    "total_items": 11,
}

GRADED_ROW: Row = RAW_ROW | {
    "listingid": 200,
    "gradingcompany": "PSA",
    "grade": "10",
    "certificationnumber": "12345678",
}


class FakeCatalogueRepository:
    def __init__(
        self,
        rows: list[Row] | None = None,
        total: int = 0,
        *,
        one: Row | None = None,
    ) -> None:
        self.rows = rows if rows is not None else []
        self.total = total
        self.one = one
        self.last_call: dict[str, Any] = {}

    def search(
        self, filters: ListingFilters, *, sort: SortKey, offset: int, limit: int
    ) -> tuple[list[Row], int]:
        self.last_call = {
            "filters": filters,
            "sort": sort,
            "offset": offset,
            "limit": limit,
        }
        return self.rows, self.total

    def get(self, listing_id: int) -> Row | None:
        self.last_call = {"listing_id": listing_id}
        return self.one

    def featured(self, limit: int) -> list[Row]:
        self.last_call = {"limit": limit}
        return self.rows

    def card_sets(self) -> list[Row]:
        return [
            {
                "setid": 100,
                "setname": "Evolving Skies",
                "releasedate": datetime(2021, 8, 27, 0, 0),
            }
        ]

    def filter_options(self) -> list[Row]:
        return [
            {"option_kind": "rarity", "option_value": "Ultra Rare"},
            {"option_kind": "rarity", "option_value": "Secret Rare"},
            {"option_kind": "variant", "option_value": "Normal"},
            {"option_kind": "condition", "option_value": "NearMint"},
            {"option_kind": "nonsense", "option_value": "ignored"},
        ]


def service_with(repository: FakeCatalogueRepository) -> CatalogueService:
    return CatalogueService(repository)  # type: ignore[arg-type]  # duck-typed stand-in


def test_money_is_a_two_decimal_string_not_a_float() -> None:
    page = service_with(FakeCatalogueRepository([RAW_ROW], 11)).search(
        ListingFilters(), sort="price_desc", page=1, page_size=12
    )
    item = page.items[0]

    assert item.asking_price == "663.00"
    assert isinstance(item.asking_price, str)
    assert item.currency == "CAD"


def test_a_datetime_from_oracle_becomes_a_plain_date() -> None:
    page = service_with(FakeCatalogueRepository([RAW_ROW], 11)).search(
        ListingFilters(), sort="price_desc", page=1, page_size=12
    )

    assert page.items[0].listed_at == date(2026, 11, 26)


def test_raw_cards_have_no_grading_block() -> None:
    page = service_with(FakeCatalogueRepository([RAW_ROW], 11)).search(
        ListingFilters(), sort="price_desc", page=1, page_size=12
    )

    assert page.items[0].grading is None


def test_graded_cards_carry_their_certification() -> None:
    page = service_with(FakeCatalogueRepository([GRADED_ROW], 1)).search(
        ListingFilters(), sort="price_desc", page=1, page_size=12
    )
    grading = page.items[0].grading

    assert grading is not None
    assert (grading.company, grading.grade) == ("PSA", "10")
    assert grading.certification_number == "12345678"


@pytest.mark.parametrize(
    ("total", "page_size", "expected_pages"),
    [(11, 12, 1), (12, 12, 1), (13, 12, 2), (24, 12, 2), (25, 12, 3), (0, 12, 0)],
)
def test_total_pages_rounds_up(total: int, page_size: int, expected_pages: int) -> None:
    page = service_with(FakeCatalogueRepository([], total)).search(
        ListingFilters(), sort="price_desc", page=1, page_size=page_size
    )

    assert page.total_pages == expected_pages


def test_page_three_asks_the_repository_to_skip_the_first_two_pages() -> None:
    repository = FakeCatalogueRepository([], 40)
    service_with(repository).search(ListingFilters(), sort="name_asc", page=3, page_size=12)

    assert repository.last_call["offset"] == 24
    assert repository.last_call["limit"] == 12


def test_missing_listing_is_a_not_found_error() -> None:
    with pytest.raises(NotFoundError):
        service_with(FakeCatalogueRepository(one=None)).get(999)


def test_detail_includes_the_fields_the_grid_leaves_out() -> None:
    detail = service_with(FakeCatalogueRepository(one=RAW_ROW)).get(100)

    assert detail.card_language == "English"
    assert detail.description == "Raw, Near Mint."
    assert detail.set_id == 100


def test_filter_options_are_grouped_and_unknown_kinds_ignored() -> None:
    options = service_with(FakeCatalogueRepository()).filter_options()

    assert options.rarities == ["Ultra Rare", "Secret Rare"]
    assert options.variants == ["Normal"]
    assert options.conditions == ["NearMint"]
