"""API-level tests for the catalogue endpoints.

The catalogue service is replaced through FastAPI's dependency overrides, so these
exercise routing, query-parameter validation and the JSON contract without a database.
The camelCase assertions are deliberate: the wire format is a contract the frontend
will be written against.
"""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import get_catalogue_service
from app.main import create_app
from app.services.catalogue import CatalogueService

from .test_catalogue_service import GRADED_ROW, RAW_ROW, FakeCatalogueRepository

MakeCatalogueClient = Callable[[FakeCatalogueRepository], TestClient]


@pytest.fixture
def make_catalogue_client(settings: Settings) -> MakeCatalogueClient:
    def _make(repository: FakeCatalogueRepository) -> TestClient:
        app = create_app(settings)
        app.dependency_overrides[get_catalogue_service] = lambda: CatalogueService(
            repository  # type: ignore[arg-type]  # duck-typed stand-in
        )
        return TestClient(app)

    return _make


def test_listings_returns_camel_case_fields(
    make_catalogue_client: MakeCatalogueClient,
) -> None:
    response = make_catalogue_client(FakeCatalogueRepository([RAW_ROW], 11)).get("/api/listings")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "page", "pageSize", "totalItems", "totalPages"}
    assert body["totalItems"] == 11
    item = body["items"][0]
    assert item["cardName"] == "Rayquaza V"
    assert item["askingPrice"] == "663.00"
    assert item["collectorNumber"] == "194/203"
    assert item["imageUrl"] is None
    assert "card_name" not in item


def test_graded_card_nests_its_grading_in_camel_case(
    make_catalogue_client: MakeCatalogueClient,
) -> None:
    response = make_catalogue_client(FakeCatalogueRepository([GRADED_ROW], 1)).get("/api/listings")

    grading = response.json()["items"][0]["grading"]
    assert grading["certificationNumber"] == "12345678"


def test_default_sort_is_price_descending(
    make_catalogue_client: MakeCatalogueClient,
) -> None:
    repository = FakeCatalogueRepository([], 0)
    make_catalogue_client(repository).get("/api/listings")

    assert repository.last_call["sort"] == "price_desc"


def test_filters_reach_the_repository(
    make_catalogue_client: MakeCatalogueClient,
) -> None:
    repository = FakeCatalogueRepository([], 0)
    make_catalogue_client(repository).get(
        "/api/listings",
        params={
            "setId": 101,
            "rarity": "Secret Rare",
            "graded": "false",
            "minPrice": "100",
            "q": "giratina",
        },
    )
    filters = repository.last_call["filters"]

    assert filters.set_id == 101
    assert filters.rarity == "Secret Rare"
    assert filters.graded is False
    assert str(filters.min_price) == "100"
    assert filters.q == "giratina"


def test_unknown_sort_key_is_rejected_before_the_database(
    make_catalogue_client: MakeCatalogueClient,
) -> None:
    """The sort key is an enum, so arbitrary text can never reach the ORDER BY."""
    repository = FakeCatalogueRepository([], 0)
    response = make_catalogue_client(repository).get(
        "/api/listings", params={"sort": "listingid; drop table listing--"}
    )

    assert response.status_code == 422
    assert repository.last_call == {}


def test_validation_errors_use_the_one_error_envelope(
    make_catalogue_client: MakeCatalogueClient,
) -> None:
    response = make_catalogue_client(FakeCatalogueRepository()).get(
        "/api/listings", params={"pageSize": 500}
    )

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "invalid_request"
    assert error["details"][0]["field"] == "pageSize"


def test_page_zero_is_rejected(make_catalogue_client: MakeCatalogueClient) -> None:
    response = make_catalogue_client(FakeCatalogueRepository()).get(
        "/api/listings", params={"page": 0}
    )

    assert response.status_code == 422


def test_listing_detail_returns_the_extra_fields(
    make_catalogue_client: MakeCatalogueClient,
) -> None:
    response = make_catalogue_client(FakeCatalogueRepository(one=RAW_ROW)).get("/api/listings/100")

    body = response.json()
    assert body["cardLanguage"] == "English"
    assert body["setId"] == 100


def test_missing_listing_is_a_404_in_the_error_envelope(
    make_catalogue_client: MakeCatalogueClient,
) -> None:
    response = make_catalogue_client(FakeCatalogueRepository(one=None)).get("/api/listings/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_featured_is_not_mistaken_for_a_listing_id(
    make_catalogue_client: MakeCatalogueClient,
) -> None:
    """/listings/featured must match its own route, not /listings/{listing_id}."""
    repository = FakeCatalogueRepository([RAW_ROW])
    response = make_catalogue_client(repository).get("/api/listings/featured")

    assert response.status_code == 200
    assert repository.last_call == {"limit": 4}
    assert response.json()[0]["cardName"] == "Rayquaza V"


def test_sets_and_filter_options_are_exposed(
    make_catalogue_client: MakeCatalogueClient,
) -> None:
    client = make_catalogue_client(FakeCatalogueRepository())

    sets = client.get("/api/sets").json()
    assert sets[0]["setName"] == "Evolving Skies"
    assert sets[0]["releaseDate"] == "2021-08-27"

    options = client.get("/api/filter-options").json()
    assert options["rarities"] == ["Ultra Rare", "Secret Rare"]
