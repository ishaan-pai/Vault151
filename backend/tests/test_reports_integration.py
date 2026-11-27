"""The five graded queries, run against real data.

These matter more than their size suggests: the reports are the only place in the
running application where MINUS, GROUP BY ... HAVING, correlated EXISTS and UNION
appear. A test per report proves each statement compiles against the live schema and
answers what it claims to.

Run with the stack up:  uv run pytest -m integration
"""

from collections.abc import Iterator

import pytest

from app.config import Settings
from app.db import Database
from app.errors import NotFoundError
from app.payments import MockPaymentProvider
from app.repositories.admin import AdminRepository
from app.repositories.orders import OrderRepository
from app.schemas.admin import GradingInput, ShipmentInput
from app.services.admin import AdminService
from app.services.checkout import CheckoutService
from app.services.reports import DEFINITIONS, ReportService

from .test_admin_integration import new_card
from .test_checkout_integration import GENERATED_ID_FLOOR, order_for

pytestmark = pytest.mark.integration


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
def reports(database: Database) -> ReportService:
    return ReportService(database)


@pytest.fixture
def settings(tmp_path: object) -> Settings:
    return Settings(media_dir=str(tmp_path))  # type: ignore[call-arg]


@pytest.fixture
def admin(database: Database, settings: Settings) -> AdminService:
    return AdminService(database, AdminRepository(), settings)


@pytest.fixture
def checkout(database: Database, settings: Settings) -> CheckoutService:
    return CheckoutService(database, OrderRepository(), MockPaymentProvider(), settings)


@pytest.fixture(autouse=True)
def clean_up(database: Database) -> Iterator[None]:
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


# --- every report runs ----------------------------------------------------------


@pytest.mark.parametrize("key", list(DEFINITIONS))
def test_every_report_compiles_and_returns_its_columns(reports: ReportService, key: str) -> None:
    """A query that does not compile against the live schema fails here, not in a demo."""
    report = reports.run(key)

    assert report.key == key
    assert report.columns, key
    assert report.row_count == len(report.rows)
    assert all(set(row) == set(report.columns) for row in report.rows)


@pytest.mark.parametrize("key", list(DEFINITIONS))
def test_every_report_carries_the_sql_it_ran(reports: ReportService, key: str) -> None:
    """The page shows its own workings, so the statement travels with the result."""
    report = reports.run(key)

    assert "select" in report.sql.lower()
    assert report.feature


def test_an_unknown_report_is_not_found(reports: ReportService) -> None:
    with pytest.raises(NotFoundError):
        reports.run("made-up-report")


# --- each report answers what it claims -----------------------------------------


def test_paid_not_shipped_lists_a_paid_order_then_drops_it_once_dispatched(
    reports: ReportService, admin: AdminService, checkout: CheckoutService
) -> None:
    """The MINUS report: paid orders, less orders that already have a shipment."""
    listing = admin.add_card(new_card())
    order = checkout.create_order(order_for([listing.listing_id]))
    checkout.pay(order.public_ref)

    before = reports.run("paid-not-shipped")
    assert any(row["orderid"] for row in before.rows)
    packing_list = before.row_count

    admin.record_shipment(
        order.public_ref, ShipmentInput(carrier="Canada Post", tracking_number="T1")
    )

    after = reports.run("paid-not-shipped")
    assert after.row_count == packing_list - 1


def test_sales_by_set_counts_only_paid_cards(
    reports: ReportService, admin: AdminService, checkout: CheckoutService
) -> None:
    """The aggregate report: COUNT, SUM and AVG grouped by set."""
    listing = admin.add_card(new_card())

    # An unpaid order must not appear: the query requires a payment row.
    order = checkout.create_order(order_for([listing.listing_id]))
    assert not any(row["setname"] == "Admin Test Set" for row in reports.run("sales-by-set").rows)

    checkout.pay(order.public_ref)

    row = next(
        row for row in reports.run("sales-by-set").rows if row["setname"] == "Admin Test Set"
    )
    assert row["cardssold"] == "1"
    assert row["total_sales_cad"] == "42.00"
    assert row["average_price_cad"] == "42.00"


def test_multi_card_orders_respects_its_bind_variable(
    reports: ReportService, admin: AdminService, checkout: CheckoutService
) -> None:
    """The HAVING report, and the only one taking a parameter."""
    first = admin.add_card(new_card())
    second = admin.add_card(new_card(collector_number="002/999"))
    order = checkout.create_order(order_for([first.listing_id, second.listing_id]))

    two_or_more = reports.run("multi-card-orders", min_cards=2)
    assert any(row["cardcount"] == "2" for row in two_or_more.rows)

    # The same order must disappear when the threshold rises above its size.
    three_or_more = reports.run("multi-card-orders", min_cards=3)
    assert not any(
        row["displayname"] == "Ash Ketchum" and row["cardcount"] == "2"
        for row in three_or_more.rows
    )
    assert order.public_ref  # the order existed throughout


def test_graded_buyers_finds_only_buyers_of_slabbed_cards(
    reports: ReportService, admin: AdminService, checkout: CheckoutService
) -> None:
    """The correlated EXISTS report."""
    raw = admin.add_card(new_card())
    raw_order = checkout.create_order(order_for([raw.listing_id], email="rawbuyer@example.com"))
    checkout.pay(raw_order.public_ref)

    assert not any(
        row["email"] == "rawbuyer@example.com" for row in reports.run("graded-buyers").rows
    )

    slabbed = admin.add_card(
        new_card(
            collector_number="003/999",
            grading=GradingInput(company="PSA", grade="10", certification_number="55551111"),
        )
    )
    graded_order = checkout.create_order(
        order_for([slabbed.listing_id], email="slabbuyer@example.com")
    )
    checkout.pay(graded_order.public_ref)

    assert any(row["email"] == "slabbuyer@example.com" for row in reports.run("graded-buyers").rows)


def test_follow_ups_lists_a_customer_once_despite_two_reasons(
    reports: ReportService, admin: AdminService, checkout: CheckoutService
) -> None:
    """The UNION report: two populations, no duplicates.

    One customer with an unpaid order AND an undelivered parcel qualifies twice,
    and must still appear once. UNION ALL would list them twice.
    """
    email = "both@example.com"

    shipped_card = admin.add_card(new_card())
    shipped = checkout.create_order(order_for([shipped_card.listing_id], email=email))
    checkout.pay(shipped.public_ref)
    admin.record_shipment(
        shipped.public_ref, ShipmentInput(carrier="Canada Post", tracking_number="T2")
    )

    unpaid_card = admin.add_card(new_card(collector_number="004/999"))
    checkout.create_order(order_for([unpaid_card.listing_id], email=email))

    matches = [row for row in reports.run("follow-ups").rows if row["email"] == email]
    assert len(matches) == 1
