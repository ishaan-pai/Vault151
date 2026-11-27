"""Integration tests against a real Oracle database.

Deselected by default. Run them with the stack up:

    uv run pytest -m integration

Skipped rather than failed when no database is reachable, so a developer without
Docker running is not blocked.
"""

from collections.abc import Iterator

import pytest

from app.config import Settings
from app.db import Database
from app.repositories.health import HealthRepository

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def database() -> Iterator[Database]:
    # Reads the same environment the application uses, so a wrong .env shows up here.
    instance = Database(Settings())  # type: ignore[call-arg]
    instance.connect()
    if not instance.is_connected:
        pytest.skip("no Oracle database reachable with the current environment")
    try:
        yield instance
    finally:
        instance.close()


def test_pool_can_round_trip_a_query(database: Database) -> None:
    assert HealthRepository(database).ping() is True


def test_graded_catalogue_view_is_readable(database: Database) -> None:
    """The application's schema user can read the graded view the catalogue needs."""
    with (
        database.connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("select count(*) from ActiveCardCatalogue")
        (count,) = cursor.fetchone()

    assert count >= 1


def test_catalogue_views_agree(database: Database) -> None:
    """CatalogueCardDetail is built on the graded view, so the two cannot diverge."""
    with (
        database.connection() as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("select count(*) from ActiveCardCatalogue")
        (graded,) = cursor.fetchone()
        cursor.execute("select count(*) from CatalogueCardDetail")
        (derived,) = cursor.fetchone()

    assert graded == derived
