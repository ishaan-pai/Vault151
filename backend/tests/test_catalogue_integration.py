"""Catalogue integration tests against the real database and the seeded data.

These are the ones that would catch a mistyped column name, a bind that never binds, or
an ORDER BY fragment that does not compile - none of which a faked repository can see.

Run with the stack up:  uv run pytest -m integration

Expectations match the seeded catalogue: 11 active listings (10 seller cards plus one
baseline demo listing), the dearest being Rayquaza V at 663.00 CAD.
"""

from collections.abc import Iterator
from decimal import Decimal

import pytest

from app.config import Settings
from app.db import Database
from app.errors import NotFoundError
from app.repositories.catalogue import SORT_FRAGMENTS, CatalogueRepository, ListingFilters
from app.services.catalogue import CatalogueService

pytestmark = pytest.mark.integration

TOTAL_ACTIVE_LISTINGS = 11
CROWN_ZENITH_LISTINGS = 4


@pytest.fixture(scope="module")
def database() -> Iterator[Database]:
    instance = Database(Settings())  # type: ignore[call-arg]
    instance.connect()
    if not instance.is_connected:
        pytest.skip("no Oracle database reachable with the current environment")
    try:
        yield instance
    finally:
        instance.close()


@pytest.fixture
def service(database: Database) -> CatalogueService:
    return CatalogueService(CatalogueRepository(database))


def test_unfiltered_search_sees_every_active_listing(service: CatalogueService) -> None:
    page = service.search(ListingFilters(), sort="price_desc", page=1, page_size=48)

    assert page.total_items == TOTAL_ACTIVE_LISTINGS
    assert len(page.items) == TOTAL_ACTIVE_LISTINGS


def test_every_sort_fragment_compiles_and_orders(service: CatalogueService) -> None:
    """Each whitelisted ORDER BY fragment must be valid SQL against the view."""
    for sort in SORT_FRAGMENTS:
        page = service.search(ListingFilters(), sort=sort, page=1, page_size=48)
        assert page.total_items == TOTAL_ACTIVE_LISTINGS, sort

    descending = service.search(ListingFilters(), sort="price_desc", page=1, page_size=48).items
    prices = [Decimal(item.asking_price) for item in descending]
    assert prices == sorted(prices, reverse=True)
    assert descending[0].card_name == "Rayquaza V"


def test_featured_is_the_four_dearest_cards(service: CatalogueService) -> None:
    featured = service.featured(4)

    assert [item.card_name for item in featured] == [
        "Rayquaza V",
        "Giratina VSTAR",
        "Charizard ex",
        "Arceus VSTAR",
    ]
    assert [item.asking_price for item in featured] == [
        "663.00",
        "375.00",
        "355.00",
        "217.00",
    ]


def test_pagination_splits_the_catalogue_without_gaps_or_repeats(
    service: CatalogueService,
) -> None:
    first = service.search(ListingFilters(), sort="price_desc", page=1, page_size=4)
    second = service.search(ListingFilters(), sort="price_desc", page=2, page_size=4)
    last = service.search(ListingFilters(), sort="price_desc", page=3, page_size=4)

    assert (first.total_pages, first.total_items) == (3, TOTAL_ACTIVE_LISTINGS)
    assert len(first.items) == 4
    assert len(last.items) == 3  # 11 does not divide evenly

    ids = [item.listing_id for item in first.items + second.items + last.items]
    assert len(ids) == len(set(ids)) == TOTAL_ACTIVE_LISTINGS


def test_page_beyond_the_end_is_empty(service: CatalogueService) -> None:
    page = service.search(ListingFilters(), sort="price_desc", page=99, page_size=12)

    assert page.items == []
    # count(*) over () rides along on the rows, so an empty page carries no total.
    # A UI that over-pages has already been told the real total by page 1.
    assert page.total_items == 0


def test_set_filter_binds(service: CatalogueService) -> None:
    """Set 101 is Crown Zenith: four Galarian Gallery golds."""
    page = service.search(ListingFilters(set_id=101), sort="price_desc", page=1, page_size=48)

    assert page.total_items == CROWN_ZENITH_LISTINGS
    assert {item.set_name for item in page.items} == {"Crown Zenith"}


def test_price_range_filter_binds(service: CatalogueService) -> None:
    page = service.search(
        ListingFilters(min_price=Decimal("150"), max_price=Decimal("400")),
        sort="price_asc",
        page=1,
        page_size=48,
    )
    prices = [Decimal(item.asking_price) for item in page.items]

    assert prices
    assert all(Decimal("150") <= price <= Decimal("400") for price in prices)


def test_text_search_matches_card_name_case_insensitively(
    service: CatalogueService,
) -> None:
    page = service.search(ListingFilters(q="giratina"), sort="price_desc", page=1, page_size=48)

    assert page.total_items == 1
    assert page.items[0].card_name == "Giratina VSTAR"


def test_graded_filter_separates_slabbed_from_raw(service: CatalogueService) -> None:
    raw = service.search(ListingFilters(graded=False), sort="price_desc", page=1, page_size=48)
    slabbed = service.search(ListingFilters(graded=True), sort="price_desc", page=1, page_size=48)

    # Nothing graded is currently listed, so every active card is raw.
    assert raw.total_items == TOTAL_ACTIVE_LISTINGS
    assert slabbed.total_items == 0
    assert all(item.grading is None for item in raw.items)


def test_filters_combine(service: CatalogueService) -> None:
    page = service.search(
        ListingFilters(set_id=101, min_price=Decimal("200")),
        sort="price_desc",
        page=1,
        page_size=48,
    )

    assert page.total_items == 2  # Giratina 375, Arceus 217


def test_detail_round_trips_a_real_listing(service: CatalogueService) -> None:
    detail = service.get(100)

    assert detail.card_name == "Rayquaza V"
    assert detail.set_name == "Evolving Skies"
    assert detail.collector_number == "194/203"
    assert detail.asking_price == "663.00"
    assert detail.card_language == "English"
    assert detail.grading is None


def test_a_withdrawn_listing_is_invisible(service: CatalogueService) -> None:
    """Listing 2 is Withdrawn in the seed, so the graded view excludes it."""
    with pytest.raises(NotFoundError):
        service.get(2)


def test_card_sets_lists_every_set_including_empty_ones(
    service: CatalogueService,
) -> None:
    sets = service.card_sets()
    names = {card_set.set_name for card_set in sets}

    assert "Crown Zenith" in names
    # 3 baseline sets + 5 of the seller's. Only 6 of the 8 have an active listing,
    # and all 8 are offered as filters - the point of decision 4.3.
    assert len(sets) == 8
    assert len({item.set_name for item in service.featured(48)}) == 6


def test_filter_options_come_from_the_live_catalogue(service: CatalogueService) -> None:
    options = service.filter_options()

    assert "Secret Rare" in options.rarities
    assert "Alternate Full Art" in options.variants
    assert options.conditions == ["NearMint"]
