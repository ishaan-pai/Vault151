"""Catalogue data access.

Reads the graded view ActiveCardCatalogue through CatalogueCardDetail. Rows come back as
dictionaries keyed by lower-case column name; turning them into response models is the
service's job, so the SQL and the API contract can change independently.
"""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

import oracledb

from ..db import Database
from ..sql import load_sql

logger = logging.getLogger(__name__)

Row = dict[str, Any]

# The sort keys the API accepts. Defined here, beside the fragments they map to,
# so the router cannot offer a key the repository does not know.
SortKey = Literal["price_desc", "price_asc", "name_asc", "newest"]

# ORDER BY cannot be a bind variable, so each sort key maps to a fixed fragment.
# The client sends a key; if it is not in here, the request never reaches the database.
# Every fragment ends with listingid to make the order total, so pagination cannot
# show the same row twice or skip one.
SORT_FRAGMENTS: dict[SortKey, str] = {
    "price_desc": "l.asking_price_cad desc, l.listingid desc",
    "price_asc": "l.asking_price_cad asc, l.listingid asc",
    "name_asc": "l.cardname asc, l.listingid asc",
    # The seller listed everything on one day, so listedat alone leaves a ten-way tie;
    # price breaks it, putting the best card first within a day.
    "newest": "l.listedat desc, l.asking_price_cad desc, l.listingid desc",
}
DEFAULT_SORT: SortKey = "price_desc"

_ORDER_BY_TOKEN = "__ORDER_BY__"  # noqa: S105 - a SQL placeholder, not a credential


@dataclass(frozen=True)
class ListingFilters:
    """Catalogue filters. Every field is optional; ``None`` disables its predicate."""

    set_id: int | None = None
    rarity: str | None = None
    variant: str | None = None
    card_condition: str | None = None
    graded: bool | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    q: str | None = None

    def as_binds(self) -> dict[str, Any]:
        return {
            "set_id": self.set_id,
            "rarity": self.rarity,
            "variant": self.variant,
            "card_condition": self.card_condition,
            # Oracle has no boolean bind type in this position; 1/0/NULL instead.
            "graded": None if self.graded is None else int(self.graded),
            "min_price": self.min_price,
            "max_price": self.max_price,
            "q": self.q,
        }


def rows_from_cursor(cursor: oracledb.Cursor) -> list[Row]:
    """Every row as a dict keyed by lower-case column name.

    ``cursor.description`` is None for a statement that returned no result set at
    all, which is not an error here - it simply means there is nothing to map.
    """
    description = cursor.description
    if description is None:
        return []
    columns = [column[0].lower() for column in description]
    return [dict(zip(columns, values, strict=True)) for values in cursor.fetchall()]


class CatalogueRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def search(
        self,
        filters: ListingFilters,
        *,
        sort: SortKey,
        offset: int,
        limit: int,
    ) -> tuple[list[Row], int]:
        """One page of matching listings, plus the total number that matched.

        The total arrives as ``total_items`` on every row, from ``count(*) over ()``,
        so no second COUNT query is needed. An empty page means zero matches.
        """
        # The endpoint validates sort against SortKey, so this lookup cannot fail
        # with anything a client sent.
        fragment = SORT_FRAGMENTS[sort]
        statement = load_sql("listingsSearch").replace(_ORDER_BY_TOKEN, fragment)
        binds = filters.as_binds() | {"row_offset": offset, "row_limit": limit}

        with (
            self._database.connection() as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(statement, binds)
            rows = rows_from_cursor(cursor)

        total = int(rows[0]["total_items"]) if rows else 0
        return rows, total

    def get(self, listing_id: int) -> Row | None:
        """One active listing, or None. Inactive listings are invisible by design."""
        with (
            self._database.connection() as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(load_sql("listingById"), {"listing_id": listing_id})
            rows = rows_from_cursor(cursor)
        return rows[0] if rows else None

    def featured(self, limit: int) -> list[Row]:
        with (
            self._database.connection() as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(load_sql("listingsFeatured"), {"row_limit": limit})
            return rows_from_cursor(cursor)

    def card_sets(self) -> list[Row]:
        with (
            self._database.connection() as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(load_sql("cardSets"))
            return rows_from_cursor(cursor)

    def filter_options(self) -> list[Row]:
        """``(option_kind, option_value)`` pairs for the filter dropdowns."""
        with (
            self._database.connection() as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(load_sql("filterOptions"))
            return rows_from_cursor(cursor)
