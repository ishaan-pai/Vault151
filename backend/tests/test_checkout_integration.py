"""Checkout against a real Oracle database.

These are the tests this project most needs. The checkout transaction is the only
place where two people can collide over one physical card, and no faked repository
can prove that the locking works - only a real database with real row locks can.

Every test restores the listing statuses and removes the rows it created, so the
suite can run repeatedly against the same seeded database.

Run with the stack up:  uv run pytest -m integration
"""

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from app.config import Settings
from app.db import Database
from app.errors import ConflictError, NotFoundError
from app.payments import MockPaymentProvider
from app.repositories.orders import OrderRepository
from app.schemas.order import CreateOrderRequest, ShippingAddress
from app.services.checkout import CheckoutService

pytestmark = pytest.mark.integration

# Seeded listings start at 100 and sequence-generated rows start at 1000, so
# anything at or above 1000 was created by a test and is safe to delete.
GENERATED_ID_FLOOR = 1000


def address() -> ShippingAddress:
    """A fresh address every call.

    Never share one instance between tests: Pydantic assigns a nested model by
    reference rather than copying it, so a test that edits request.shipping_address
    would quietly edit every later test's address too.
    """
    return ShippingAddress(
        recipient_name="Ash Ketchum",
        street="1 Pallet Lane",
        city="Toronto",
        province="Ontario",
        postal_code="M5V 2T6",
        country="CA",
    )


def order_for(listing_ids: list[int], email: str = "buyer@example.com") -> CreateOrderRequest:
    return CreateOrderRequest(
        email=email,
        display_name="Ash Ketchum",
        listing_ids=listing_ids,
        shipping_address=address(),
    )


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
def settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


@pytest.fixture
def service(database: Database, settings: Settings) -> CheckoutService:
    return CheckoutService(database, OrderRepository(), MockPaymentProvider(), settings)


@pytest.fixture(autouse=True)
def restore_database(database: Database) -> Iterator[None]:
    """Snapshot listing statuses, then undo everything the test did.

    Without this the first test to sell a card would starve every test after it.
    """
    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute("select listingid, listingstatus from listing")
        before = dict(cursor.fetchall())

    yield

    with database.transaction() as connection, connection.cursor() as cursor:
        cursor.execute("delete from payment where orderid >= :floor", {"floor": GENERATED_ID_FLOOR})
        cursor.execute(
            "delete from orderline where orderid >= :floor",
            {"floor": GENERATED_ID_FLOOR},
        )
        cursor.execute(
            "delete from salesorder where orderid >= :floor",
            {"floor": GENERATED_ID_FLOOR},
        )
        cursor.execute(
            "delete from customer where customerid >= :floor",
            {"floor": GENERATED_ID_FLOOR},
        )
        for listing_id, status in before.items():
            cursor.execute(
                "update listing set listingstatus = :status where listingid = :id",
                {"status": status, "id": listing_id},
            )


def listing_status(database: Database, listing_id: int) -> str:
    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "select listingstatus from listing where listingid = :id",
            {"id": listing_id},
        )
        (status,) = cursor.fetchone()
    return str(status)


# --- placing an order -----------------------------------------------------------


def test_placing_an_order_reserves_its_cards(service: CheckoutService, database: Database) -> None:
    summary = service.create_order(order_for([100, 101]))

    assert summary.status == "AwaitingPayment"
    assert len(summary.public_ref) == 32  # rawtohex(sys_guid())
    assert [item.listing_id for item in summary.items] == [100, 101]
    assert [item.line_no for item in summary.items] == [1, 2]
    assert listing_status(database, 100) == "Reserved"
    assert listing_status(database, 101) == "Reserved"


def test_the_order_total_is_the_cards_plus_shipping(service: CheckoutService) -> None:
    summary = service.create_order(order_for([100, 101]))

    assert summary.subtotal == "1038.00"  # 663.00 + 375.00
    assert summary.shipping_fee == "15.00"  # flat within Canada
    assert summary.total == "1053.00"
    assert summary.currency == "CAD"


def test_shipping_to_the_us_costs_more(service: CheckoutService) -> None:
    request = order_for([100])
    request.shipping_address.country = "US"
    request.shipping_address.province = "New York"

    summary = service.create_order(request)

    assert summary.shipping_fee == "30.00"


def test_an_unreserved_card_stays_in_the_catalogue(
    service: CheckoutService, database: Database
) -> None:
    service.create_order(order_for([100]))

    assert listing_status(database, 101) == "Active"


def test_the_reservation_has_an_expiry(service: CheckoutService) -> None:
    summary = service.create_order(order_for([100]))

    assert summary.expires_at is not None
    assert summary.expires_at > summary.placed_at


def test_a_second_order_cannot_take_a_reserved_card(service: CheckoutService) -> None:
    service.create_order(order_for([100]))

    with pytest.raises(ConflictError, match="no longer available"):
        service.create_order(order_for([100], email="second@example.com"))


def test_a_nonexistent_listing_is_rejected(service: CheckoutService) -> None:
    with pytest.raises(NotFoundError):
        service.create_order(order_for([999_999]))


def test_a_withdrawn_listing_cannot_be_bought(service: CheckoutService) -> None:
    """Listing 2 is Withdrawn in the seed; it is not in the catalogue either."""
    with pytest.raises(ConflictError):
        service.create_order(order_for([2]))


def test_the_same_card_twice_is_rejected(service: CheckoutService) -> None:
    with pytest.raises(ConflictError, match="twice"):
        service.create_order(order_for([100, 100]))


def test_we_refuse_to_ship_where_we_do_not_ship(service: CheckoutService) -> None:
    request = order_for([100])
    # Bypass the schema's Literal, which is what the API boundary would reject,
    # to prove the service refuses too rather than trusting its caller.
    request.shipping_address.country = "FR"  # type: ignore[assignment]

    with pytest.raises(ConflictError, match="do not currently ship"):
        service.create_order(request)


def test_a_failed_order_leaves_nothing_behind(service: CheckoutService, database: Database) -> None:
    """The second card is unavailable, so the first must not stay reserved."""
    service.create_order(order_for([101]))

    with pytest.raises(ConflictError):
        service.create_order(order_for([100, 101], email="third@example.com"))

    # 100 was locked first and would have been reserved had the transaction not
    # rolled back when 101 turned out to be taken.
    assert listing_status(database, 100) == "Active"


def test_one_customer_row_per_email(service: CheckoutService, database: Database) -> None:
    service.create_order(order_for([100], email="repeat@example.com"))
    service.create_order(order_for([101], email="repeat@example.com"))

    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "select count(*) from customer where lower(email) = :email",
            {"email": "repeat@example.com"},
        )
        (count,) = cursor.fetchone()

    assert count == 1


# --- the race -------------------------------------------------------------------


def test_two_buyers_racing_for_one_card_produce_exactly_one_order(
    database: Database, settings: Settings
) -> None:
    """The point of SELECT ... FOR UPDATE.

    Two real connections attempt the same card at the same moment. One must win and
    one must be told it is gone; the card must not be sold twice, and there must not
    be two orders holding it.
    """

    def buy(email: str) -> object:
        service = CheckoutService(database, OrderRepository(), MockPaymentProvider(), settings)
        try:
            return service.create_order(order_for([100], email=email))
        except ConflictError as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(buy, ["racer-one@example.com", "racer-two@example.com"]))

    winners = [r for r in results if not isinstance(r, Exception)]
    losers = [r for r in results if isinstance(r, ConflictError)]

    assert len(winners) == 1, f"expected one winner, got {results}"
    assert len(losers) == 1
    assert listing_status(database, 100) == "Reserved"

    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "select count(*) from orderline where listingid = 100 and orderid >= :floor",
            {"floor": GENERATED_ID_FLOOR},
        )
        (lines,) = cursor.fetchone()

    assert lines == 1, "the card ended up on two orders"


# --- expiry ---------------------------------------------------------------------


def backdate(database: Database, public_ref: str, days: int = 1) -> None:
    """Push an order into the past so its hold has lapsed."""
    with database.transaction() as connection, connection.cursor() as cursor:
        cursor.execute(
            "update salesorder set placedat = placedat - :days where publicref = :ref",
            {"days": days, "ref": public_ref},
        )


def test_an_expired_reservation_returns_the_card_and_cancels_the_order(
    service: CheckoutService, database: Database
) -> None:
    summary = service.create_order(order_for([100]))
    assert listing_status(database, 100) == "Reserved"

    backdate(database, summary.public_ref)

    # Expiry is evaluated on read: nothing scheduled, nothing in the background.
    after = service.find_order(summary.public_ref, "buyer@example.com")

    assert after.status == "Cancelled"
    assert after.expires_at is None
    assert listing_status(database, 100) == "Active"


def test_a_card_freed_by_expiry_can_be_bought_by_someone_else(
    service: CheckoutService, database: Database
) -> None:
    first = service.create_order(order_for([100]))
    backdate(database, first.public_ref)

    second = service.create_order(order_for([100], email="patient@example.com"))

    assert second.status == "AwaitingPayment"
    assert listing_status(database, 100) == "Reserved"


def test_an_expired_order_cannot_be_paid(service: CheckoutService, database: Database) -> None:
    summary = service.create_order(order_for([100]))
    backdate(database, summary.public_ref)

    with pytest.raises(ConflictError, match="cancelled"):
        service.pay(summary.public_ref)


# --- payment --------------------------------------------------------------------


def test_paying_marks_the_order_paid_and_the_cards_sold(
    service: CheckoutService, database: Database
) -> None:
    placed = service.create_order(order_for([100, 101]))

    paid = service.pay(placed.public_ref)

    assert paid.status == "Paid"
    assert paid.payment is not None
    assert paid.payment.method == "mock"
    assert paid.payment.amount == "1053.00"
    assert paid.payment.reference.startswith("mock_")
    assert paid.expires_at is None
    assert listing_status(database, 100) == "Sold"
    assert listing_status(database, 101) == "Sold"


def test_a_sold_card_leaves_the_catalogue(service: CheckoutService, database: Database) -> None:
    """The graded view only contains Active listings, so this needs no extra filter."""
    placed = service.create_order(order_for([100]))
    service.pay(placed.public_ref)

    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute("select count(*) from ActiveCardCatalogue where listingid = 100")
        (visible,) = cursor.fetchone()

    assert visible == 0


def test_paying_twice_records_one_payment(service: CheckoutService, database: Database) -> None:
    """A double-clicked Pay button must not charge twice.

    payment_order_uq in the baseline schema is what guarantees it: the second insert
    cannot land, so the guard is the database rather than application logic.
    """
    placed = service.create_order(order_for([100]))

    first = service.pay(placed.public_ref)
    second = service.pay(placed.public_ref)

    assert first.payment is not None
    assert second.payment is not None
    assert first.payment.reference == second.payment.reference

    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "select count(*) from payment where orderid >= :floor",
            {"floor": GENERATED_ID_FLOOR},
        )
        (payments,) = cursor.fetchone()

    assert payments == 1


def test_two_simultaneous_payments_record_one_payment(
    service: CheckoutService, database: Database, settings: Settings
) -> None:
    """The same guarantee, but genuinely concurrent rather than sequential."""
    placed = service.create_order(order_for([100]))

    def pay() -> object:
        own = CheckoutService(database, OrderRepository(), MockPaymentProvider(), settings)
        try:
            return own.pay(placed.public_ref)
        except Exception as exc:  # noqa: BLE001 - the test asserts on the outcome
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [f.result() for f in [pool.submit(pay), pool.submit(pay)]]

    assert all(not isinstance(r, Exception) for r in results), results

    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "select count(*) from payment where orderid >= :floor",
            {"floor": GENERATED_ID_FLOOR},
        )
        (payments,) = cursor.fetchone()

    assert payments == 1


def test_paying_an_unknown_reference_is_not_found(service: CheckoutService) -> None:
    with pytest.raises(NotFoundError):
        service.pay("0" * 32)


# --- lookup ---------------------------------------------------------------------


def test_lookup_needs_the_matching_email(service: CheckoutService) -> None:
    placed = service.create_order(order_for([100], email="owner@example.com"))

    found = service.find_order(placed.public_ref, "owner@example.com")
    assert found.public_ref == placed.public_ref
    assert [item.card_name for item in found.items] == ["Rayquaza V"]

    with pytest.raises(NotFoundError):
        service.find_order(placed.public_ref, "nosy@example.com")


def test_lookup_is_case_insensitive_about_the_email(service: CheckoutService) -> None:
    placed = service.create_order(order_for([100], email="Owner@Example.com"))

    found = service.find_order(placed.public_ref, "owner@example.com")

    assert found.public_ref == placed.public_ref


def test_a_paid_order_shows_its_receipt(service: CheckoutService) -> None:
    """The receipt comes from the graded view PaidOrderReceipts."""
    placed = service.create_order(order_for([100]))
    service.pay(placed.public_ref)

    found = service.find_order(placed.public_ref, "buyer@example.com")

    assert found.payment is not None
    assert Decimal(found.payment.amount) == Decimal(found.total)
