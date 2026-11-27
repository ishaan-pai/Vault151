"""Repository for the health check.

The only repository that deliberately converts a failure into a return value: a health
check exists to report "down" rather than to propagate it. The reason is always logged,
so nothing is silently swallowed.
"""

import logging

import oracledb

from ..db import Database
from ..errors import DatabaseUnavailableError
from ..sql import load_sql

logger = logging.getLogger(__name__)


class HealthRepository:
    def __init__(self, database: Database) -> None:
        self._database = database

    def ping(self) -> bool:
        """True when a pooled connection can run ``select 1 from dual``."""
        try:
            with (
                self._database.connection() as connection,
                connection.cursor() as cursor,
            ):
                cursor.execute(load_sql("healthCheck"))
                row = cursor.fetchone()
        except (DatabaseUnavailableError, oracledb.Error) as exc:
            logger.warning("health check could not reach the database: %s", exc)
            return False
        return row is not None and row[0] == 1
