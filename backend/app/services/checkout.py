"""Checkout, payment and order lookup.

Each public method here is exactly one database transaction. The repository never
commits; this layer opens the transaction, and anything raised inside it rolls the
whole thing back, so a half-placed order cannot exist.
"""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import oracledb

from ..config import Settings
from ..db import Database
from ..errors import ConflictError, NotFoundError
from ..payments import PaymentProvider
from ..repositories.catalogue import Row
from ..repositories.orders import OrderRepository
from ..schemas.order import (
    CreateOrderRequest,
    OrderLineItem,
    OrderSummary,
    PaymentSummary,
    ShippingAddress,
)

logger = logging.getLogger(__name__)

CURRENCY = "CAD"

STATUS_AWAITING = "AwaitingPayment"
STATUS_PAID = "Paid"
LISTING_ACTIVE = "Active"
LISTING_RESERVED = "Reserved"
LISTING_SOLD = "Sold"


def _money(value: Decimal | int | float | None) -> str:
    return f"{Decimal(str(value or 0)):.2f}"


def _naive_utc(moment: datetime) -> datetime:
    """Oracle DATE columns hold no timezone, so store a naive UTC value."""
    return moment.astimezone(UTC).replace(tzinfo=None)


class CheckoutService:
    def __init__(
        self,
        database: Database,
        repository: OrderRepository,
        payments: PaymentProvider,
        settings: Settings,
    ) -> None:
        self._database = database
        self._repository = repository
        self._payments = payments
        self._settings = settings

    # --- helpers ----------------------------------------------------------------

    @property
    def _reservation_window(self) -> timedelta:
        return timedelta(minutes=self._settings.reservation_minutes)

    def _cutoff(self) -> datetime:
        """Orders placed before this have lost their hold."""
        return _naive_utc(datetime.now(UTC)) - self._reservation_window

    def shipping_fee_for(self, country: str) -> Decimal:
        fee = self._settings.shipping_fees.get(country.upper())
        if fee is None:
            raise ConflictError(f"We do not currently ship to {country}.")
        return fee

    # --- checkout ---------------------------------------------------------------

    def create_order(self, request: CreateOrderRequest) -> OrderSummary:
        """Place an order, reserving its cards. One transaction, all or nothing.

        The listings are locked in ascending id order. Locking in a consistent order
        is what stops two simultaneous carts each holding a card the other needs and
        deadlocking; it also means the loser of a race fails cleanly on the first
        contested card rather than halfway through.
        """
        if len(set(request.listing_ids)) != len(request.listing_ids):
            raise ConflictError("The same card appears twice in your cart. Each card is unique.")

        fee = self.shipping_fee_for(request.shipping_address.country)
        now = _naive_utc(datetime.now(UTC))

        with self._database.transaction() as connection:
            # Free anything whose hold has lapsed first, so a card abandoned by
            # someone else can be bought in this very transaction.
            self._repository.release_expired(connection, self._cutoff())

            priced: list[tuple[int, Decimal]] = []
            for listing_id in sorted(set(request.listing_ids)):
                row = self._repository.lock_listing(connection, listing_id)
                if row is None:
                    raise NotFoundError(f"No listing {listing_id} exists.")
                status = str(row["listingstatus"])
                if status != LISTING_ACTIVE:
                    # Someone else got there first, or it was never for sale.
                    raise ConflictError(f"Listing {listing_id} is no longer available.")
                priced.append((listing_id, Decimal(str(row["askingprice"]))))

            customer_id = self._upsert_customer(
                connection,
                email=str(request.email),
                display_name=request.display_name,
                now=now,
            )

            order_id, public_ref = self._repository.insert_order(
                connection,
                customer_id=customer_id,
                placed_at=now,
                shipping_fee=fee,
                address=request.shipping_address.model_dump(),
            )

            for line_no, (listing_id, price) in enumerate(priced, start=1):
                self._repository.insert_order_line(
                    connection,
                    order_id=order_id,
                    line_no=line_no,
                    listing_id=listing_id,
                    agreed_price=price,
                )
                self._repository.set_listing_status(
                    connection, listing_id=listing_id, status=LISTING_RESERVED
                )

            logger.info(
                "order placed",
                extra={"order_id": order_id, "lines": len(priced)},
            )
            return self._build_summary(connection, public_ref=public_ref)

    def _upsert_customer(
        self,
        connection: oracledb.Connection,
        *,
        email: str,
        display_name: str,
        now: datetime,
    ) -> int:
        """One customer row per email address, reused on a return visit."""
        existing = self._repository.find_customer_id(connection, email)
        if existing is not None:
            return existing
        try:
            return self._repository.insert_customer(
                connection, display_name=display_name, email=email, joined_at=now
            )
        except oracledb.IntegrityError:
            # customer_email_uq fired: another checkout inserted the same email
            # between our select and our insert. Their row is as good as ours.
            found = self._repository.find_customer_id(connection, email)
            if found is None:
                raise
            return found

    # --- payment ----------------------------------------------------------------

    def pay(self, public_ref: str) -> OrderSummary:
        """Take payment for an order and mark its cards sold.

        Locking the order row is what serialises two simultaneous Pay requests. The
        second one then sees status Paid and is answered with the payment that
        already exists, so a double-clicked button is a no-op rather than an error.
        """
        with self._database.transaction() as connection:
            self._repository.release_expired(connection, self._cutoff())

            order = self._repository.lock_order(connection, public_ref)
            if order is None:
                raise NotFoundError("No order with that reference.")

            order_id = int(order["orderid"])
            status = str(order["orderstatus"])

            if status == STATUS_PAID:
                # Already paid: answer with the original result, do not charge again.
                return self._build_summary(connection, public_ref=public_ref)

            if status != STATUS_AWAITING:
                raise ConflictError(f"This order is {status.lower()} and cannot be paid.")

            amount = self._order_total(connection, order_id, order)
            result = self._payments.charge(order_ref=public_ref, amount=amount, currency=CURRENCY)

            try:
                self._repository.insert_payment(
                    connection,
                    order_id=order_id,
                    paid_at=_naive_utc(result.paid_at),
                    amount=amount,
                    method=self._payments.name,
                    reference=result.reference,
                )
            except oracledb.IntegrityError:
                # payment_order_uq: a payment landed between our status read and
                # this insert. The database refused the duplicate, which is the
                # behaviour we want; report the existing one.
                logger.info(
                    "duplicate payment rejected by the database", extra={"order_id": order_id}
                )
                return self._build_summary(connection, public_ref=public_ref)

            self._repository.set_order_status(connection, order_id=order_id, status=STATUS_PAID)
            for listing_id in self._repository.listing_ids_for_order(connection, order_id):
                self._repository.set_listing_status(
                    connection, listing_id=listing_id, status=LISTING_SOLD
                )

            logger.info("order paid", extra={"order_id": order_id})
            return self._build_summary(connection, public_ref=public_ref)

    def _order_total(self, connection: oracledb.Connection, order_id: int, order: Row) -> Decimal:
        """Subtotal from the order lines plus shipping. No tax is charged."""
        items = self._repository.order_items(connection, order_id)
        subtotal = sum((Decimal(str(item["agreed_price_cad"])) for item in items), Decimal("0"))
        return subtotal + Decimal(str(order["shippingfee"]))

    # --- lookup -----------------------------------------------------------------

    def find_order(self, public_ref: str, email: str) -> OrderSummary:
        """Guest order lookup: the reference and the email must both match."""
        with self._database.transaction() as connection:
            self._repository.release_expired(connection, self._cutoff())
            summary = self._build_summary(connection, public_ref=public_ref, email=email)
        return summary

    # --- assembly ---------------------------------------------------------------

    def _build_summary(
        self,
        connection: oracledb.Connection,
        *,
        public_ref: str,
        email: str | None = None,
    ) -> OrderSummary:
        order = (
            self._repository.find_order(connection, public_ref=public_ref, email=email)
            if email is not None
            else self._repository.find_order_by_ref(connection, public_ref)
        )

        if order is None:
            # Same message whether the reference is wrong or the email does not
            # match it: saying which would let someone probe for valid references.
            raise NotFoundError("No order matches that reference and email address.")

        order_id = int(order["orderid"])
        items = [
            OrderLineItem(
                line_no=int(item["lineno"]),
                listing_id=int(item["listingid"]),
                card_name=str(item["cardname"]),
                card_language=str(item["cardlanguage"]),
                variant=str(item["variant"]),
                card_condition=str(item["cardcondition"]),
                agreed_price=_money(item["agreed_price_cad"]),
            )
            for item in self._repository.order_items(connection, order_id)
        ]
        subtotal = sum((Decimal(item.agreed_price) for item in items), Decimal("0"))
        shipping = Decimal(str(order["shippingfee"]))
        status = str(order["orderstatus"])
        placed_at = order["placedat"]

        receipt = self._repository.receipt(connection, order_id)
        payment = (
            PaymentSummary(
                paid_at=receipt["paidat"],
                amount=_money(receipt["amount_cad"]),
                method=str(receipt["method"]),
                reference=str(receipt["paymentreference"]),
            )
            if receipt
            else None
        )

        return OrderSummary(
            public_ref=str(order["publicref"]),
            status=status,
            placed_at=placed_at,
            # Only an unpaid order is still holding its cards.
            expires_at=(
                placed_at + self._reservation_window if status == STATUS_AWAITING else None
            ),
            items=items,
            subtotal=_money(subtotal),
            shipping_fee=_money(shipping),
            total=_money(subtotal + shipping),
            currency=CURRENCY,
            shipping_address=ShippingAddress(
                recipient_name=str(order["recipientname"]),
                street=str(order["street"]),
                city=str(order["city"]),
                province=order["province"],
                postal_code=str(order["postalcode"]),
                country=str(order["country"]),  # type: ignore[arg-type]
            ),
            email=str(order["email"]),
            payment=payment,
        )
