"""Admin inventory and fulfilment against a real database.

Covers the paths that touch several tables at once: adding a card creates rows in
cardset, cardprinting, cardcopy and listing, and deleting one has to unpick that
again without breaking a foreign key.

Run with the stack up:  uv run pytest -m integration
"""

from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest

from app.config import Settings
from app.db import Database
from app.errors import ConflictError, NotFoundError
from app.media import ImageTooLargeError, UnsupportedImageError, detect_extension
from app.payments import MockPaymentProvider
from app.repositories.admin import AdminRepository
from app.repositories.orders import OrderRepository
from app.schemas.admin import GradingInput, NewCardRequest, ShipmentInput
from app.services.admin import AdminService
from app.services.checkout import CheckoutService

from .test_checkout_integration import GENERATED_ID_FLOOR, order_for

pytestmark = pytest.mark.integration

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def new_card(**overrides: object) -> NewCardRequest:
    payload: dict[str, object] = {
        "set_name": "Admin Test Set",
        "set_release_date": date(2026, 1, 1),
        "card_name": "Test Pikachu",
        "collector_number": "001/999",
        "card_language": "English",
        "variant": "Normal",
        "rarity": "Rare",
        "card_condition": "NearMint",
        "description": "A card created by the admin tests.",
        "asking_price": Decimal("42.00"),
    }
    payload.update(overrides)
    return NewCardRequest(**payload)  # type: ignore[arg-type]


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
def settings(tmp_path: object) -> Settings:
    # Uploads land in a temporary directory, never the real media volume.
    return Settings(media_dir=str(tmp_path))  # type: ignore[call-arg]


@pytest.fixture
def admin(database: Database, settings: Settings) -> AdminService:
    return AdminService(database, AdminRepository(), settings)


@pytest.fixture
def checkout(database: Database, settings: Settings) -> CheckoutService:
    return CheckoutService(database, OrderRepository(), MockPaymentProvider(), settings)


@pytest.fixture(autouse=True)
def clean_up(database: Database) -> Iterator[None]:
    """Remove everything the admin tests created, newest tables first."""
    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute("select listingid, listingstatus from listing")
        before = dict(cursor.fetchall())

    yield

    floor = {"floor": GENERATED_ID_FLOOR}
    with database.transaction() as connection, connection.cursor() as cursor:
        for statement in (
            "delete from shipment where orderid >= :floor",
            "delete from payment where orderid >= :floor",
            "delete from orderline where orderid >= :floor",
            "delete from salesorder where orderid >= :floor",
            "delete from customer where customerid >= :floor",
            "delete from listing where listingid >= :floor",
            "delete from gradedcardcopy where copyid >= :floor",
            "delete from cardcopy where copyid >= :floor",
            "delete from cardprinting where printingid >= :floor",
            "delete from cardset where setid >= :floor",
        ):
            cursor.execute(statement, floor)
        for listing_id, status in before.items():
            cursor.execute(
                "update listing set listingstatus = :status where listingid = :id",
                {"status": status, "id": listing_id},
            )


# --- adding inventory -----------------------------------------------------------


def test_adding_a_card_creates_every_row_it_needs(admin: AdminService) -> None:
    listing = admin.add_card(new_card())

    assert listing.listing_id >= GENERATED_ID_FLOOR
    assert listing.card_name == "Test Pikachu"
    assert listing.set_name == "Admin Test Set"
    assert listing.asking_price == "42.00"
    assert listing.status == "Active"
    assert listing.image_url is None


def test_a_new_card_appears_in_the_catalogue(admin: AdminService, database: Database) -> None:
    listing = admin.add_card(new_card())

    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "select count(*) from CatalogueCardDetail where listingid = :id",
            {"id": listing.listing_id},
        )
        (visible,) = cursor.fetchone()

    assert visible == 1


def test_a_second_card_reuses_the_set_and_printing(admin: AdminService, database: Database) -> None:
    """cardprinting_version_uq would reject a duplicate printing outright."""
    first = admin.add_card(new_card())
    second = admin.add_card(new_card(description="A second copy of the same card."))

    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute("select count(*) from cardset where setname = 'Admin Test Set'")
        (sets,) = cursor.fetchone()
        cursor.execute("select count(*) from cardprinting where collectornumber = '001/999'")
        (printings,) = cursor.fetchone()

    assert (sets, printings) == (1, 1)
    assert first.listing_id != second.listing_id
    assert first.copy_id != second.copy_id  # two physical cards


def test_a_graded_card_stores_its_certification(admin: AdminService, database: Database) -> None:
    listing = admin.add_card(
        new_card(grading=GradingInput(company="PSA", grade="10", certification_number="99887766"))
    )

    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "select gradingcompany, grade from gradedcardcopy where copyid = :id",
            {"id": listing.copy_id},
        )
        row = cursor.fetchone()

    assert row == ("PSA", "10")


# --- editing --------------------------------------------------------------------


def test_the_price_can_be_changed(admin: AdminService) -> None:
    listing = admin.add_card(new_card())

    updated = admin.set_price(listing.listing_id, Decimal("55.50"))

    assert updated.asking_price == "55.50"


def test_disabling_hides_a_card_and_re_enabling_restores_it(
    admin: AdminService, database: Database
) -> None:
    listing = admin.add_card(new_card())

    disabled = admin.set_status(listing.listing_id, "Withdrawn")
    assert disabled.status == "Withdrawn"

    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "select count(*) from ActiveCardCatalogue where listingid = :id",
            {"id": listing.listing_id},
        )
        (visible,) = cursor.fetchone()
    assert visible == 0

    assert admin.set_status(listing.listing_id, "Active").status == "Active"


def test_a_reserved_card_cannot_be_edited(admin: AdminService, checkout: CheckoutService) -> None:
    listing = admin.add_card(new_card())
    checkout.create_order(order_for([listing.listing_id]))

    with pytest.raises(ConflictError, match="reserved"):
        admin.set_price(listing.listing_id, Decimal("1.00"))


# --- deleting -------------------------------------------------------------------


def test_deleting_removes_the_listing_and_its_card(admin: AdminService, database: Database) -> None:
    listing = admin.add_card(new_card())

    admin.delete_listing(listing.listing_id)

    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "select count(*) from listing where listingid = :id",
            {"id": listing.listing_id},
        )
        (listings,) = cursor.fetchone()
        cursor.execute("select count(*) from cardcopy where copyid = :id", {"id": listing.copy_id})
        (copies,) = cursor.fetchone()

    assert (listings, copies) == (0, 0)


def test_deleting_a_graded_card_removes_its_certification_too(
    admin: AdminService, database: Database
) -> None:
    """gradedcardcopy_copy_fk points at cardcopy, so it must go first."""
    listing = admin.add_card(
        new_card(grading=GradingInput(company="PSA", grade="9", certification_number="123"))
    )

    admin.delete_listing(listing.listing_id)

    with database.connection() as connection, connection.cursor() as cursor:
        cursor.execute(
            "select count(*) from gradedcardcopy where copyid = :id",
            {"id": listing.copy_id},
        )
        (grades,) = cursor.fetchone()

    assert grades == 0


def test_an_ordered_card_cannot_be_deleted(admin: AdminService, checkout: CheckoutService) -> None:
    """orderline_listing_fk protects the customer's order history."""
    listing = admin.add_card(new_card())
    order = checkout.create_order(order_for([listing.listing_id]))
    checkout.pay(order.public_ref)

    with pytest.raises(ConflictError, match="Disable it instead"):
        admin.delete_listing(listing.listing_id)


def test_an_ordered_card_reports_itself_as_not_deletable(
    admin: AdminService, checkout: CheckoutService
) -> None:
    """The flag the admin UI uses to grey the Delete button out."""
    listing = admin.add_card(new_card())
    assert listing.deletable is True

    checkout.create_order(order_for([listing.listing_id]))

    assert admin.get_listing(listing.listing_id).deletable is False


def test_deleting_something_that_is_not_there(admin: AdminService) -> None:
    with pytest.raises(NotFoundError):
        admin.delete_listing(987_654)


# --- photos ---------------------------------------------------------------------


def test_a_photo_can_be_attached_after_listing(admin: AdminService) -> None:
    listing = admin.add_card(new_card())
    assert listing.image_url is None

    with_photo = admin.attach_image(listing.listing_id, PNG)

    assert with_photo.image_url is not None
    assert with_photo.image_url.startswith("/media/card-")
    assert with_photo.image_url.endswith(".png")


def test_replacing_a_photo_gives_a_new_url(admin: AdminService) -> None:
    """A new filename each time, so a cached copy of the old photo is not served."""
    listing = admin.add_card(new_card())
    first = admin.attach_image(listing.listing_id, PNG).image_url
    second = admin.attach_image(listing.listing_id, PNG).image_url

    assert first != second


def test_a_disguised_file_is_rejected(admin: AdminService) -> None:
    listing = admin.add_card(new_card())

    with pytest.raises(UnsupportedImageError):
        admin.attach_image(listing.listing_id, b"MZ\x90\x00 an executable, not a png")


def test_an_oversized_image_is_rejected(admin: AdminService) -> None:
    listing = admin.add_card(new_card())

    with pytest.raises(ImageTooLargeError):
        admin.attach_image(listing.listing_id, b"\x89PNG\r\n\x1a\n" + b"0" * 6_000_000)


def test_magic_bytes_identify_the_real_type() -> None:
    assert detect_extension(b"\xff\xd8\xff\xe0") == "jpg"
    assert detect_extension(b"\x89PNG\r\n\x1a\n") == "png"
    assert detect_extension(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "webp"


# --- fulfilment -----------------------------------------------------------------


def test_a_paid_order_can_be_dispatched_and_delivered(
    admin: AdminService, checkout: CheckoutService
) -> None:
    listing = admin.add_card(new_card())
    order = checkout.create_order(order_for([listing.listing_id]))
    checkout.pay(order.public_ref)

    shipped = admin.record_shipment(
        order.public_ref, ShipmentInput(carrier="Canada Post", tracking_number="CP123")
    )
    assert shipped.carrier == "Canada Post"
    assert shipped.delivered_at is None

    delivered = admin.mark_delivered(order.public_ref)
    assert delivered.delivered_at is not None
    assert delivered.delivered_at >= delivered.shipped_at


def test_an_unpaid_order_cannot_be_dispatched(
    admin: AdminService, checkout: CheckoutService
) -> None:
    listing = admin.add_card(new_card())
    order = checkout.create_order(order_for([listing.listing_id]))

    with pytest.raises(ConflictError, match="unpaid"):
        admin.record_shipment(
            order.public_ref, ShipmentInput(carrier="Canada Post", tracking_number="X")
        )


def test_an_order_cannot_be_dispatched_twice(
    admin: AdminService, checkout: CheckoutService
) -> None:
    """shipment_order_uq allows one shipment per order."""
    listing = admin.add_card(new_card())
    order = checkout.create_order(order_for([listing.listing_id]))
    checkout.pay(order.public_ref)
    admin.record_shipment(
        order.public_ref, ShipmentInput(carrier="Canada Post", tracking_number="CP1")
    )

    with pytest.raises(ConflictError, match="already been dispatched"):
        admin.record_shipment(
            order.public_ref,
            ShipmentInput(carrier="Canada Post", tracking_number="CP2"),
        )


def test_delivery_before_dispatch_is_impossible(
    admin: AdminService, checkout: CheckoutService
) -> None:
    listing = admin.add_card(new_card())
    order = checkout.create_order(order_for([listing.listing_id]))
    checkout.pay(order.public_ref)

    with pytest.raises(ConflictError, match="not been dispatched"):
        admin.mark_delivered(order.public_ref)


def test_the_order_list_rolls_up_each_order(admin: AdminService, checkout: CheckoutService) -> None:
    listing = admin.add_card(new_card())
    order = checkout.create_order(order_for([listing.listing_id]))

    rows = admin.orders()
    mine = next(row for row in rows if row.public_ref == order.public_ref)

    assert mine.card_count == 1
    assert mine.subtotal == "42.00"
    assert mine.total == "57.00"  # 42.00 plus CA$15 shipping
    assert mine.shipment is None
