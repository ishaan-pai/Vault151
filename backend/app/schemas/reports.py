"""Admin reporting models.

One generic envelope rather than five typed shapes. The reports exist to show the
SQL behind them, their columns come straight from the query, and the page renders
them all with one table - so a per-report model would be five near-identical classes
that still had to be rendered generically.
"""

from .catalogue import CamelModel


class ReportSummary(CamelModel):
    """A report in the menu, before it is run."""

    key: str
    title: str
    description: str
    feature: str
    """The SQL feature the query demonstrates, e.g. "MINUS"."""


class Report(ReportSummary):
    """A report with its results and the statement that produced them."""

    sql: str
    """The exact text sent to Oracle, so the page can show its own workings."""

    columns: list[str]
    rows: list[dict[str, str]]
    row_count: int
