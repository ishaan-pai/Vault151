"""Write-side data access: checkout, payment and order lookup.

Nothing here commits. Every method takes the connection its caller is holding, so one
service call is one transaction and the boundary stays visible at the service.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import oracledb

from ..sql import load_sql
from .catalogue import Row, rows_from_cursor

logger = logging.getLogger(__name__)


class OrderRepository:
    """All statements take an explicit connection: the service owns the transaction."""

    # --- expiry -----------------------------------------------------------------

    def release_expired(self, connection: oracledb.Connection, cutoff: datetime) -> int:
        """Free cards held by unpaid orders older than the cutoff, and cancel them.

        Listings first, then orders: the listing statement reads the orders the
        second statement is about to cancel. Returns how many cards were released.
        """
        with connection.cursor() as cursor:
            cursor.execute(load_sql("releaseExpiredListings"), {"cutoff": cutoff})
            released = int(cursor.rowcount)
            cursor.execute(load_sql("releaseExpiredOrders"), {"cutoff": cutoff})
        if released:
            logger.info("released expired reservations", extra={"listings": released})
        return released

    # --- checkout ---------------------------------------------------------------

    def lock_listing(self, connection: oracledb.Connection, listing_id: int) -> Row | None:
        """SELECT ... FOR UPDATE one listing. None if no such listing exists."""
        with connection.cursor() as cursor:
            cursor.execute(load_sql("lockListingForUpdate"), {"listing_id": listing_id})
            rows = rows_from_cursor(cursor)
        return rows[0] if rows else None

    def find_customer_id(self, connection: oracledb.Connection, email: str) -> int | None:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("findCustomerByEmail"), {"email": email})
            rows = rows_from_cursor(cursor)
        return int(rows[0]["customerid"]) if rows else None

    def insert_customer(
        self,
        connection: oracledb.Connection,
        *,
        display_name: str,
        email: str,
        joined_at: datetime,
    ) -> int:
        with connection.cursor() as cursor:
            customer_id = cursor.var(int)
            cursor.execute(
                load_sql("insertCustomer"),
                {
                    "display_name": display_name,
                    "email": email,
                    "joined_at": joined_at,
                    "customer_id": customer_id,
                },
            )
            return int(customer_id.getvalue()[0])

    def insert_order(
        self,
        connection: oracledb.Connection,
        *,
        customer_id: int,
        placed_at: datetime,
        shipping_fee: Decimal,
        address: dict[str, Any],
    ) -> tuple[int, str]:
        """Insert the order; the database supplies both the id and the public ref."""
        with connection.cursor() as cursor:
            order_id = cursor.var(int)
            public_ref = cursor.var(str)
            cursor.execute(
                load_sql("insertOrder"),
                {
                    "customer_id": customer_id,
                    "placed_at": placed_at,
                    "shipping_fee": shipping_fee,
                    "recipient_name": address["recipient_name"],
                    "street": address["street"],
                    "city": address["city"],
                    "province": address["province"],
                    "postal_code": address["postal_code"],
                    "country": address["country"],
                    "order_id": order_id,
                    "public_ref": public_ref,
                },
            )
            return int(order_id.getvalue()[0]), str(public_ref.getvalue()[0])

    def insert_order_line(
        self,
        connection: oracledb.Connection,
        *,
        order_id: int,
        line_no: int,
        listing_id: int,
        agreed_price: Decimal,
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                load_sql("insertOrderLine"),
                {
                    "order_id": order_id,
                    "line_no": line_no,
                    "listing_id": listing_id,
                    "agreed_price": agreed_price,
                },
            )

    def set_listing_status(
        self, connection: oracledb.Connection, *, listing_id: int, status: str
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                load_sql("updateListingStatus"),
                {"status": status, "listing_id": listing_id},
            )

    # --- payment ----------------------------------------------------------------

    def lock_order(self, connection: oracledb.Connection, public_ref: str) -> Row | None:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("lockOrderByPublicRef"), {"public_ref": public_ref})
            rows = rows_from_cursor(cursor)
        return rows[0] if rows else None

    def listing_ids_for_order(self, connection: oracledb.Connection, order_id: int) -> list[int]:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("listingsForOrder"), {"order_id": order_id})
            return [int(row["listingid"]) for row in rows_from_cursor(cursor)]

    def insert_payment(
        self,
        connection: oracledb.Connection,
        *,
        order_id: int,
        paid_at: datetime,
        amount: Decimal,
        method: str,
        reference: str,
    ) -> int:
        """Insert the payment row.

        Raises oracledb.IntegrityError if one already exists for this order, which is
        the baseline's payment_order_uq doing the idempotency work.
        """
        with connection.cursor() as cursor:
            payment_id = cursor.var(int)
            cursor.execute(
                load_sql("insertPayment"),
                {
                    "order_id": order_id,
                    "paid_at": paid_at,
                    "amount": amount,
                    "method": method,
                    "payment_reference": reference,
                    "payment_id": payment_id,
                },
            )
            return int(payment_id.getvalue()[0])

    def payment_for_order(self, connection: oracledb.Connection, order_id: int) -> Row | None:
        with connection.cursor() as cursor:
            cursor.execute(load_sql("paymentByOrderId"), {"order_id": order_id})
            rows = rows_from_cursor(cursor)
        return rows[0] if rows else None

    def set_order_status(
        self, connection: oracledb.Connection, *, order_id: int, status: str
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                load_sql("updateOrderStatus"),
                {"status": status, "order_id": order_id},
            )

    # --- lookup -----------------------------------------------------------------

    def find_order(
        self, connection: oracledb.Connection, *, public_ref: str, email: str
    ) -> Row | None:
        with connection.cursor() as cursor:
            cursor.execute(
                load_sql("orderByPublicRef"),
                {"public_ref": public_ref, "email": email},
            )
            rows = rows_from_cursor(cursor)
        return rows[0] if rows else None

    def find_order_by_ref(self, connection: oracledb.Connection, public_ref: str) -> Row | None:
        """Order by reference alone, with no email check.

        Only for use straight after this process created or paid the order. Guest
        lookup must go through find_order(), which requires the email as well.
        """
        with connection.cursor() as cursor:
            cursor.execute(load_sql("orderByPublicRefOnly"), {"public_ref": public_ref})
            rows = rows_from_cursor(cursor)
        return rows[0] if rows else None

    def order_items(self, connection: oracledb.Connection, order_id: int) -> list[Row]:
        """From the graded view CustomerOrderItems."""
        with connection.cursor() as cursor:
            cursor.execute(load_sql("orderItems"), {"order_id": order_id})
            return rows_from_cursor(cursor)

    def receipt(self, connection: oracledb.Connection, order_id: int) -> Row | None:
        """From the graded view PaidOrderReceipts."""
        with connection.cursor() as cursor:
            cursor.execute(load_sql("receiptByOrderId"), {"order_id": order_id})
            rows = rows_from_cursor(cursor)
        return rows[0] if rows else None
