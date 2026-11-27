"""Seller admin: inventory, listings, orders and shipments."""

import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import oracledb

from ..config import Settings
from ..db import Database
from ..errors import ConflictError, NotFoundError
from ..media import save_card_image
from ..repositories.admin import AdminRepository
from ..repositories.catalogue import Row
from ..schemas.admin import (
    AdminListing,
    AdminOrderRow,
    NewCardRequest,
    ShipmentInfo,
    ShipmentInput,
)
from ..sql import load_sql

logger = logging.getLogger(__name__)

STATUS_ACTIVE = "Active"
STATUS_WITHDRAWN = "Withdrawn"
# A listing may only be changed while it is one of these: editing a Reserved card
# would change what a buyer is about to pay, and a Sold one would rewrite history.
EDITABLE_STATUSES = frozenset({STATUS_ACTIVE, STATUS_WITHDRAWN})


def _money(value: Decimal | int | float | None) -> str:
    return f"{Decimal(str(value or 0)):.2f}"


def _naive_utc(moment: datetime) -> datetime:
    return moment.astimezone(UTC).replace(tzinfo=None)


class AdminService:
    def __init__(self, database: Database, repository: AdminRepository, settings: Settings) -> None:
        self._database = database
        self._repository = repository
        self._settings = settings

    # --- inventory --------------------------------------------------------------

    def add_card(self, request: NewCardRequest) -> AdminListing:
        """Add one physical card and list it, in a single transaction.

        The set and printing are reused when they already exist. Without that,
        adding a second Crown Zenith card would either duplicate the set or hit
        cardprinting_version_uq and fail.
        """
        with self._database.transaction() as connection:
            set_id = self._repository.find_set_id(connection, request.set_name)
            if set_id is None:
                set_id = self._repository.insert_set(
                    connection,
                    set_name=request.set_name,
                    release_date=request.set_release_date,
                )

            printing_id = self._repository.find_printing_id(
                connection,
                set_id=set_id,
                collector_number=request.collector_number,
                card_language=request.card_language,
                variant=request.variant,
            )
            if printing_id is None:
                printing_id = self._repository.insert_printing(
                    connection,
                    set_id=set_id,
                    card_name=request.card_name,
                    collector_number=request.collector_number,
                    card_language=request.card_language,
                    variant=request.variant,
                    rarity=request.rarity,
                )

            copy_id = self._repository.insert_copy(
                connection,
                printing_id=printing_id,
                card_condition=request.card_condition,
                description=request.description,
                image_url=None,
            )

            if request.grading is not None:
                self._repository.insert_grading(
                    connection,
                    copy_id=copy_id,
                    company=request.grading.company,
                    grade=request.grading.grade,
                    certification_number=request.grading.certification_number,
                )

            listing_id = self._repository.insert_listing(
                connection,
                copy_id=copy_id,
                asking_price=request.asking_price,
                listed_at=date.today(),
            )
            logger.info("card added", extra={"listing_id": listing_id})
            return self._listing(connection, listing_id)

    def get_listing(self, listing_id: int) -> AdminListing:
        with self._database.connection() as connection:
            return self._listing(connection, listing_id)

    def set_price(self, listing_id: int, price: Decimal) -> AdminListing:
        with self._database.transaction() as connection:
            self._require_editable(connection, listing_id)
            self._repository.update_price(connection, listing_id=listing_id, price=price)
            return self._listing(connection, listing_id)

    def set_status(self, listing_id: int, status: str) -> AdminListing:
        """Disable (Withdrawn) or re-enable (Active) a listing. Always reversible."""
        with self._database.transaction() as connection:
            current = self._require_editable(connection, listing_id)
            if current == status:
                return self._listing(connection, listing_id)
            with connection.cursor() as cursor:
                cursor.execute(
                    load_sql("updateListingStatus"),
                    {"status": status, "listing_id": listing_id},
                )
            logger.info(
                "listing status changed",
                extra={"listing_id": listing_id, "status": status},
            )
            return self._listing(connection, listing_id)

    def delete_listing(self, listing_id: int) -> None:
        """Remove a listing entirely, and its card when nothing else needs it.

        Refused once the listing appears on any order: orderline_listing_fk points
        here, and deleting it would tear a hole in a real customer's order history.
        Disabling is the right answer in that case, and it is always available.
        """
        with self._database.transaction() as connection:
            listing = self._repository.listing_for_edit(connection, listing_id)
            if listing is None:
                raise NotFoundError(f"No listing {listing_id} exists.")

            if self._repository.order_line_count(connection, listing_id) > 0:
                raise ConflictError(
                    "This card has been ordered, so it cannot be deleted without "
                    "damaging that order. Disable it instead."
                )

            copy_id = int(listing["copyid"])
            self._repository.delete_listing(connection, listing_id)

            # If that was the copy's only listing, the physical card goes too -
            # otherwise a mistyped entry would leave an orphan behind forever.
            if self._repository.listing_count_for_copy(connection, copy_id) == 0:
                self._repository.delete_copy(connection, copy_id)

            logger.info("listing deleted", extra={"listing_id": listing_id})

    def attach_image(self, listing_id: int, content: bytes) -> AdminListing:
        """Attach or replace a card's photo, at any time after listing."""
        with self._database.transaction() as connection:
            listing = self._repository.listing_for_edit(connection, listing_id)
            if listing is None:
                raise NotFoundError(f"No listing {listing_id} exists.")
            copy_id = int(listing["copyid"])

            url = save_card_image(
                content=content,
                copy_id=copy_id,
                media_dir=Path(self._settings.media_dir),
                url_prefix=self._settings.media_url_prefix,
                max_bytes=self._settings.max_upload_bytes,
            )
            self._repository.update_image(connection, copy_id=copy_id, image_url=url)
            return self._listing(connection, listing_id)

    # --- orders -----------------------------------------------------------------

    def orders(self, status: str | None = None) -> list[AdminOrderRow]:
        with self._database.connection() as connection:
            rows = self._repository.orders(connection, status)
        return [self._order_row(row) for row in rows]

    def record_shipment(self, public_ref: str, shipment: ShipmentInput) -> ShipmentInfo:
        with self._database.transaction() as connection:
            order = self._repository.order_by_ref(connection, public_ref)
            if order is None:
                raise NotFoundError("No order with that reference.")
            order_id = int(order["orderid"])
            status = str(order["orderstatus"])

            if status not in {"Paid", "Shipped", "Delivered"}:
                raise ConflictError(f"This order is {status.lower()} and unpaid.")
            if self._repository.shipment_for_order(connection, order_id) is not None:
                raise ConflictError("This order has already been dispatched.")

            now = _naive_utc(datetime.now(UTC))
            self._repository.insert_shipment(
                connection,
                order_id=order_id,
                carrier=shipment.carrier,
                tracking_number=shipment.tracking_number,
                shipped_at=now,
            )
            self._set_order_status(connection, order_id, "Shipped")
            return ShipmentInfo(
                carrier=shipment.carrier,
                tracking_number=shipment.tracking_number,
                shipped_at=now,
                delivered_at=None,
            )

    def mark_delivered(self, public_ref: str) -> ShipmentInfo:
        with self._database.transaction() as connection:
            order = self._repository.order_by_ref(connection, public_ref)
            if order is None:
                raise NotFoundError("No order with that reference.")
            order_id = int(order["orderid"])

            existing = self._repository.shipment_for_order(connection, order_id)
            if existing is None:
                raise ConflictError("This order has not been dispatched yet.")
            if existing["deliveredat"] is not None:
                raise ConflictError("This order is already marked delivered.")

            now = _naive_utc(datetime.now(UTC))
            self._repository.mark_delivered(connection, order_id=order_id, delivered_at=now)
            self._set_order_status(connection, order_id, "Delivered")
            return ShipmentInfo(
                carrier=str(existing["carrier"]),
                tracking_number=str(existing["trackingnumber"]),
                shipped_at=existing["shippedat"],
                delivered_at=now,
            )

    # --- helpers ----------------------------------------------------------------

    def _set_order_status(
        self, connection: oracledb.Connection, order_id: int, status: str
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                load_sql("updateOrderStatus"),
                {"status": status, "order_id": order_id},
            )

    def _require_editable(self, connection: oracledb.Connection, listing_id: int) -> str:
        listing = self._repository.listing_for_edit(connection, listing_id)
        if listing is None:
            raise NotFoundError(f"No listing {listing_id} exists.")
        status = str(listing["listingstatus"])
        if status not in EDITABLE_STATUSES:
            raise ConflictError(f"This card is {status.lower()} and cannot be changed.")
        return status

    def _listing(self, connection: oracledb.Connection, listing_id: int) -> AdminListing:
        row = self._repository.listing_for_edit(connection, listing_id)
        if row is None:
            raise NotFoundError(f"No listing {listing_id} exists.")
        status = str(row["listingstatus"])
        ordered = self._repository.order_line_count(connection, listing_id)
        return AdminListing(
            listing_id=int(row["listingid"]),
            copy_id=int(row["copyid"]),
            card_name=str(row["cardname"]),
            set_name=str(row["setname"]),
            collector_number=str(row["collectornumber"]),
            variant=str(row["variant"]),
            rarity=str(row["rarity"]),
            card_condition=str(row["cardcondition"]),
            description=str(row["description"]),
            asking_price=_money(row["askingprice"]),
            status=status,
            listed_at=row["listedat"].date()
            if isinstance(row["listedat"], datetime)
            else row["listedat"],
            image_url=row["imageurl"],
            editable=status in EDITABLE_STATUSES,
            deletable=status in EDITABLE_STATUSES and ordered == 0,
        )

    def _order_row(self, row: Row) -> AdminOrderRow:
        subtotal = Decimal(str(row["subtotal"] or 0))
        shipping = Decimal(str(row["shippingfee"] or 0))
        shipment = (
            ShipmentInfo(
                carrier="",
                tracking_number="",
                shipped_at=row["shippedat"],
                delivered_at=row["deliveredat"],
            )
            if row["shipmentid"] is not None
            else None
        )
        return AdminOrderRow(
            public_ref=str(row["publicref"]),
            status=str(row["orderstatus"]),
            placed_at=row["placedat"],
            customer_name=str(row["displayname"]),
            email=str(row["email"]),
            card_count=int(row["card_count"] or 0),
            subtotal=_money(subtotal),
            shipping_fee=_money(shipping),
            total=_money(subtotal + shipping),
            shipment=shipment,
        )
