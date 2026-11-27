"""Write-side data access for the seller's admin area.

As with orders, nothing here commits: each method takes the connection its caller is
holding, so one service call is one transaction.
"""

import logging
from datetime import date, datetime
from decimal import Decimal

import oracledb

from ..sql import load_sql
from .catalogue import Row, rows_from_cursor

logger = logging.getLogger(__name__)


class AdminRepository:
    # --- inventory --------------------------------------------------------------

    def find_set_id(self, connection: oracledb.Connection, set_name: str) -> int | None:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("adminFindOrCreateSet"), {"set_name": set_name})
            rows = rows_from_cursor(cursor)
        return int(rows[0]["setid"]) if rows else None

    def insert_set(
        self, connection: oracledb.Connection, *, set_name: str, release_date: date
    ) -> int:
        with connection.cursor() as cursor:
            set_id = cursor.var(int)
            cursor.execute(
                load_sql("adminInsertSet"),
                {"set_name": set_name, "release_date": release_date, "set_id": set_id},
            )
            return int(set_id.getvalue()[0])

    def find_printing_id(
        self,
        connection: oracledb.Connection,
        *,
        set_id: int,
        collector_number: str,
        card_language: str,
        variant: str,
    ) -> int | None:
        with connection.cursor() as cursor:
            cursor.execute(
                load_sql("adminFindPrinting"),
                {
                    "set_id": set_id,
                    "collector_number": collector_number,
                    "card_language": card_language,
                    "variant": variant,
                },
            )
            rows = rows_from_cursor(cursor)
        return int(rows[0]["printingid"]) if rows else None

    def insert_printing(
        self,
        connection: oracledb.Connection,
        *,
        set_id: int,
        card_name: str,
        collector_number: str,
        card_language: str,
        variant: str,
        rarity: str,
    ) -> int:
        with connection.cursor() as cursor:
            printing_id = cursor.var(int)
            cursor.execute(
                load_sql("adminInsertPrinting"),
                {
                    "set_id": set_id,
                    "card_name": card_name,
                    "collector_number": collector_number,
                    "card_language": card_language,
                    "variant": variant,
                    "rarity": rarity,
                    "printing_id": printing_id,
                },
            )
            return int(printing_id.getvalue()[0])

    def insert_copy(
        self,
        connection: oracledb.Connection,
        *,
        printing_id: int,
        card_condition: str,
        description: str,
        image_url: str | None,
    ) -> int:
        with connection.cursor() as cursor:
            copy_id = cursor.var(int)
            cursor.execute(
                load_sql("adminInsertCopy"),
                {
                    "printing_id": printing_id,
                    "card_condition": card_condition,
                    "description": description,
                    "image_url": image_url,
                    "copy_id": copy_id,
                },
            )
            return int(copy_id.getvalue()[0])

    def insert_grading(
        self,
        connection: oracledb.Connection,
        *,
        copy_id: int,
        company: str,
        grade: str,
        certification_number: str,
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                load_sql("adminInsertGrading"),
                {
                    "copy_id": copy_id,
                    "grading_company": company,
                    "grade": grade,
                    "certification_number": certification_number,
                },
            )

    def insert_listing(
        self,
        connection: oracledb.Connection,
        *,
        copy_id: int,
        asking_price: Decimal,
        listed_at: date,
    ) -> int:
        with connection.cursor() as cursor:
            listing_id = cursor.var(int)
            cursor.execute(
                load_sql("adminInsertListing"),
                {
                    "copy_id": copy_id,
                    "asking_price": asking_price,
                    "listed_at": listed_at,
                    "listing_id": listing_id,
                },
            )
            return int(listing_id.getvalue()[0])

    # --- editing ----------------------------------------------------------------

    def listing_for_edit(self, connection: oracledb.Connection, listing_id: int) -> Row | None:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("adminListingForEdit"), {"listing_id": listing_id})
            rows = rows_from_cursor(cursor)
        return rows[0] if rows else None

    def update_price(
        self, connection: oracledb.Connection, *, listing_id: int, price: Decimal
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                load_sql("adminUpdateListingPrice"),
                {"listing_id": listing_id, "asking_price": price},
            )

    def update_image(
        self, connection: oracledb.Connection, *, copy_id: int, image_url: str
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                load_sql("adminUpdateCopyImage"),
                {"copy_id": copy_id, "image_url": image_url},
            )

    def order_line_count(self, connection: oracledb.Connection, listing_id: int) -> int:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("adminCountOrderLinesForListing"), {"listing_id": listing_id})
            rows = rows_from_cursor(cursor)
        return int(rows[0]["line_count"]) if rows else 0

    def listing_count_for_copy(self, connection: oracledb.Connection, copy_id: int) -> int:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("adminCountListingsForCopy"), {"copy_id": copy_id})
            rows = rows_from_cursor(cursor)
        return int(rows[0]["listing_count"]) if rows else 0

    def delete_listing(self, connection: oracledb.Connection, listing_id: int) -> None:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("adminDeleteListing"), {"listing_id": listing_id})

    def delete_copy(self, connection: oracledb.Connection, copy_id: int) -> None:
        """Removes the grading row first: gradedcardcopy_copy_fk points at cardcopy."""
        with connection.cursor() as cursor:
            cursor.execute(load_sql("adminDeleteGrading"), {"copy_id": copy_id})
            cursor.execute(load_sql("adminDeleteCopy"), {"copy_id": copy_id})

    # --- orders -----------------------------------------------------------------

    def orders(self, connection: oracledb.Connection, status: str | None) -> list[Row]:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("adminOrders"), {"status": status})
            return rows_from_cursor(cursor)

    def order_by_ref(self, connection: oracledb.Connection, public_ref: str) -> Row | None:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("adminOrderByRef"), {"public_ref": public_ref})
            rows = rows_from_cursor(cursor)
        return rows[0] if rows else None

    def shipment_for_order(self, connection: oracledb.Connection, order_id: int) -> Row | None:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("adminShipmentForOrder"), {"order_id": order_id})
            rows = rows_from_cursor(cursor)
        return rows[0] if rows else None

    def insert_shipment(
        self,
        connection: oracledb.Connection,
        *,
        order_id: int,
        carrier: str,
        tracking_number: str,
        shipped_at: datetime,
    ) -> int:
        with connection.cursor() as cursor:
            shipment_id = cursor.var(int)
            cursor.execute(
                load_sql("adminInsertShipment"),
                {
                    "order_id": order_id,
                    "carrier": carrier,
                    "tracking_number": tracking_number,
                    "shipped_at": shipped_at,
                    "shipment_id": shipment_id,
                },
            )
            return int(shipment_id.getvalue()[0])

    def mark_delivered(
        self, connection: oracledb.Connection, *, order_id: int, delivered_at: datetime
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                load_sql("adminMarkDelivered"),
                {"order_id": order_id, "delivered_at": delivered_at},
            )
