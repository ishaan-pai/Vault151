"""Unit tests for /health. No database required."""

from collections.abc import Callable

from fastapi.testclient import TestClient

from app.sql import load_sql

from .conftest import FakeDatabase

MakeClient = Callable[[FakeDatabase], TestClient]


def test_health_is_ok_when_the_database_answers(make_client: MakeClient) -> None:
    database = FakeDatabase(row=(1,))
    response = make_client(database).get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_runs_the_statement_from_the_sql_file(make_client: MakeClient) -> None:
    database = FakeDatabase(row=(1,))
    make_client(database).get("/api/health")

    assert database.last_connection is not None
    assert database.last_connection.cursor_obj.executed == load_sql("healthCheck")


def test_health_is_degraded_when_the_pool_is_unavailable(make_client: MakeClient) -> None:
    response = make_client(FakeDatabase(available=False)).get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unreachable"}


def test_health_is_degraded_when_the_query_returns_nothing(make_client: MakeClient) -> None:
    """A connection that answers with no row is not a healthy database."""
    response = make_client(FakeDatabase(row=None)).get("/api/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unreachable"}


def test_unknown_path_is_a_404(make_client: MakeClient) -> None:
    assert make_client(FakeDatabase()).get("/api/nope").status_code == 404
