"""Admin reporting.

Each report is one of the graded Assignment 5 queries, run against live data. They
are the only place in the running application where MINUS, GROUP BY ... HAVING,
correlated EXISTS and UNION appear, so they are what demonstrates the database work
the project is marked on.
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from ..db import Database
from ..errors import NotFoundError
from ..repositories.catalogue import Row
from ..schemas.reports import Report, ReportSummary
from ..sql import load_sql

logger = logging.getLogger(__name__)

ReportKey = Literal[
    "paid-not-shipped",
    "sales-by-set",
    "multi-card-orders",
    "graded-buyers",
    "follow-ups",
]


class ReportDefinition(ReportSummary):
    statement: str
    """The name of the .sql file holding the query."""


DEFINITIONS: dict[str, ReportDefinition] = {
    "paid-not-shipped": ReportDefinition(
        key="paid-not-shipped",
        title="Paid, not yet shipped",
        description="Orders with a recorded payment but no shipment. The packing list.",
        feature="MINUS",
        statement="reportPaidNotShipped",
    ),
    "sales-by-set": ReportDefinition(
        key="sales-by-set",
        title="Sales by set",
        description=(
            "Cards sold, total and average price for each set, from agreed prices "
            "rather than list prices. Shipping is excluded."
        ),
        feature="GROUP BY with COUNT, SUM and AVG",
        statement="reportSalesBySet",
    ),
    "multi-card-orders": ReportDefinition(
        key="multi-card-orders",
        title="Orders with several cards",
        description="Non-cancelled orders holding at least the chosen number of cards.",
        feature="GROUP BY ... HAVING, with a bind variable for the threshold",
        statement="reportMultiCardOrders",
    ),
    "graded-buyers": ReportDefinition(
        key="graded-buyers",
        title="Buyers of graded cards",
        description="Customers who have bought at least one slabbed card.",
        feature="Correlated EXISTS subquery",
        statement="reportGradedBuyers",
    ),
    "follow-ups": ReportDefinition(
        key="follow-ups",
        title="Payment and delivery follow-ups",
        description=(
            "Everyone awaiting payment, plus everyone whose parcel has not arrived, "
            "each listed once."
        ),
        feature="UNION of two populations",
        statement="reportFollowUps",
    ),
}


# Money columns are named with this suffix throughout the schema and the reports.
MONEY_SUFFIX = "_cad"


def _display(column: str, value: object) -> str:
    """Render one cell. Money keeps two decimals; dates lose the time of day.

    The column name decides what is money, not the Python type. SUM() and AVG()
    produce a NUMBER with no declared scale, which the driver hands back as an int
    or a float, so a total of 42.00 would otherwise print as "42" and an average of
    42.333... would print in full. Formatting here rather than with TO_CHAR in the
    query keeps the five statements identical to the graded originals, which is the
    point of being able to show them.
    """
    if value is None:
        return ""
    if column.endswith(MONEY_SUFFIX) or isinstance(value, Decimal):
        return f"{Decimal(str(value)):.2f}"
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


class ReportService:
    def __init__(self, database: Database) -> None:
        self._database = database

    def menu(self) -> list[ReportSummary]:
        return [
            ReportSummary(key=d.key, title=d.title, description=d.description, feature=d.feature)
            for d in DEFINITIONS.values()
        ]

    def run(self, key: str, *, min_cards: int = 2) -> Report:
        definition = DEFINITIONS.get(key)
        if definition is None:
            raise NotFoundError(f"No report called {key}.")

        statement = load_sql(definition.statement)
        binds: dict[str, object] = {}
        if definition.key == "multi-card-orders":
            binds["min_cards"] = min_cards

        with (
            self._database.connection() as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(statement, binds)
            description = cursor.description or []
            columns = [column[0].lower() for column in description]
            rows: list[Row] = [
                dict(zip(columns, values, strict=True)) for values in cursor.fetchall()
            ]

        logger.info("report run", extra={"report": key, "rows": len(rows)})
        return Report(
            key=definition.key,
            title=definition.title,
            description=definition.description,
            feature=definition.feature,
            sql=statement,
            columns=columns,
            rows=[{name: _display(name, row[name]) for name in columns} for row in rows],
            row_count=len(rows),
        )
