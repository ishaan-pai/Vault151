"""Test fixtures.

Unit tests build the real application with a stand-in database, so routing, dependency
injection, the repository and the SQL loader are all exercised without Oracle running.
The client is deliberately *not* used as a context manager: that is what would run the
lifespan and try to open a real connection pool.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from types import TracebackType
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings
from app.errors import DatabaseUnavailableError
from app.main import create_app


class FakeCursor:
    """Just enough of oracledb.Cursor for the statements under test."""

    def __init__(self, row: tuple[Any, ...] | None) -> None:
        self._row = row
        self.executed: str | None = None
        self.binds: Any = None

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def execute(self, statement: str, binds: Any = None) -> None:
        self.executed = statement
        self.binds = binds

    def fetchone(self) -> tuple[Any, ...] | None:
        return self._row


class FakeConnection:
    def __init__(self, row: tuple[Any, ...] | None) -> None:
        self.cursor_obj = FakeCursor(row)
        self.rolled_back = False

    def cursor(self) -> FakeCursor:
        return self.cursor_obj

    def rollback(self) -> None:
        self.rolled_back = True


class FakeDatabase:
    """Stands in for Database; its connections never leave the process."""

    def __init__(
        self,
        row: tuple[Any, ...] | None = (1,),
        *,
        available: bool = True,
    ) -> None:
        self.row = row
        self.available = available
        self.last_connection: FakeConnection | None = None

    def connect(self) -> None:
        return None

    def close(self) -> None:
        return None

    @contextmanager
    def connection(self) -> Iterator[FakeConnection]:
        if not self.available:
            raise DatabaseUnavailableError("The database connection pool is not available.")
        connection = FakeConnection(self.row)
        self.last_connection = connection
        yield connection


@pytest.fixture
def settings() -> Settings:
    return Settings(
        app_env="dev",
        app_user="cardshop",
        app_user_password=SecretStr("not-a-real-password"),  # noqa: S106 - test fixture
    )


@pytest.fixture
def make_client(settings: Settings) -> Callable[[FakeDatabase], TestClient]:
    """Build a TestClient backed by the given stand-in database."""

    def _make(database: FakeDatabase) -> TestClient:
        app = create_app(settings)
        app.state.database = database
        return TestClient(app)

    return _make
