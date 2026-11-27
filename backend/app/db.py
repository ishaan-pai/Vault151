"""Oracle connection pooling.

python-oracledb in thin mode: pure Python, so no Oracle Instant Client is needed in
the image. Calls are synchronous; FastAPI runs the sync endpoints that use them in a
threadpool, so the event loop is never blocked.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

import oracledb

from .config import Settings
from .errors import DatabaseUnavailableError

logger = logging.getLogger(__name__)

# How long acquire() waits for a free connection before giving up, rather than
# hanging a request forever when the database is unreachable.
_ACQUIRE_TIMEOUT_SECONDS = 5


class Database:
    """Owns the connection pool for the lifetime of the application."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pool: oracledb.ConnectionPool | None = None

    def connect(self) -> None:
        """Create the pool.

        A failure here is logged but not raised: the application still starts, and
        /health reports the database as unreachable. Refusing to boot would mean no
        health endpoint to ask, which is worse to operate.
        """
        settings = self._settings
        try:
            self._pool = oracledb.create_pool(
                user=settings.app_user,
                password=settings.app_user_password.get_secret_value(),
                dsn=settings.db_dsn,
                min=settings.db_pool_min,
                max=settings.db_pool_max,
                increment=settings.db_pool_increment,
                getmode=oracledb.POOL_GETMODE_TIMEDWAIT,
                wait_timeout=_ACQUIRE_TIMEOUT_SECONDS * 1000,
            )
        except oracledb.Error:
            # dsn only: never log the credentials alongside it.
            logger.exception("could not create the connection pool for %s", settings.db_dsn)
            self._pool = None
            return
        logger.info(
            "connection pool ready",
            extra={
                "dsn": settings.db_dsn,
                "pool_min": settings.db_pool_min,
                "pool_max": settings.db_pool_max,
            },
        )

    @property
    def is_connected(self) -> bool:
        """Whether a pool exists. Says nothing about the database still answering."""
        return self._pool is not None

    def close(self) -> None:
        if self._pool is None:
            return
        self._pool.close(force=True)
        self._pool = None
        logger.info("connection pool closed")

    @contextmanager
    def transaction(self) -> Iterator[oracledb.Connection]:
        """A connection that commits on success and rolls back on any exception.

        Reads use connection() and never commit. Writes use this, so a multi-row
        change - lock the listings, insert the order and its lines, flip the
        listings to Reserved - either lands whole or not at all. Nothing in the
        repositories commits on its own, so the transaction boundary is always
        visible here at the service call site.
        """
        with self.connection() as connection:
            try:
                yield connection
            except Exception:
                connection.rollback()
                raise
            connection.commit()

    @contextmanager
    def connection(self) -> Iterator[oracledb.Connection]:
        """Borrow a connection, returning it to the pool on the way out.

        Rolls back on any exception, so a failed multi-statement write can never
        leave half its work behind for the next borrower of that session.
        """
        if self._pool is None:
            raise DatabaseUnavailableError("The database connection pool is not available.")
        try:
            connection = self._pool.acquire()
        except oracledb.Error as exc:
            raise DatabaseUnavailableError("Could not acquire a database connection.") from exc

        try:
            yield connection
        except Exception:
            connection.rollback()
            raise
        finally:
            self._pool.release(connection)
