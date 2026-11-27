"""Admin authentication, with no database involved.

The question these answer is the one that matters for an admin area: can anything be
reached without signing in?
"""

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings
from app.main import create_app
from app.security import LoginThrottle, hash_password, verify_password

PASSWORD = "correct-horse-battery-staple"  # noqa: S105 - a test fixture, not a secret

# Every admin route, so a new one cannot quietly ship without a guard.
PROTECTED: list[tuple[str, str]] = [
    ("get", "/api/admin/session"),
    ("post", "/api/admin/cards"),
    ("get", "/api/admin/listings/100"),
    ("patch", "/api/admin/listings/100"),
    ("post", "/api/admin/listings/100/status?status=Withdrawn"),
    ("delete", "/api/admin/listings/100"),
    ("post", "/api/admin/listings/100/image"),
    ("get", "/api/admin/orders"),
    ("post", "/api/admin/orders/00112233445566778899aabbccddeeff/shipment"),
    ("post", "/api/admin/orders/00112233445566778899aabbccddeeff/delivered"),
]


@pytest.fixture(scope="module")
def admin_settings() -> Settings:
    return Settings(
        app_env="dev",
        app_user="cardshop",
        app_user_password=SecretStr("not-a-real-password"),  # noqa: S106
        admin_username="seller",
        admin_password_hash=SecretStr(hash_password(PASSWORD)),
        admin_jwt_secret=SecretStr("a-test-signing-secret-of-at-least-32-chars"),
    )


@pytest.fixture
def client(admin_settings: Settings) -> TestClient:
    app = create_app(admin_settings)
    app.state.login_throttle = LoginThrottle()
    return TestClient(app)


def sign_in(client: TestClient, password: str = PASSWORD) -> httpx.Response:
    # TestClient's verbs are typed as returning Any, so pin the type here once
    # rather than scattering ignores through the assertions below.
    response: httpx.Response = client.post(
        "/api/admin/login", json={"username": "seller", "password": password}
    )
    return response


# --- hashing --------------------------------------------------------------------


def test_the_hash_is_not_the_password() -> None:
    stored = hash_password(PASSWORD)

    assert PASSWORD not in stored
    assert stored.startswith("$argon2")


def test_verification_accepts_only_the_right_password() -> None:
    stored = hash_password(PASSWORD)

    assert verify_password(PASSWORD, stored) is True
    assert verify_password("nearly-right", stored) is False


def test_two_hashes_of_one_password_differ() -> None:
    """Argon2 salts each hash, so identical passwords do not look identical."""
    assert hash_password(PASSWORD) != hash_password(PASSWORD)


# --- the guard ------------------------------------------------------------------


@pytest.mark.parametrize(("method", "path"), PROTECTED)
def test_every_admin_route_rejects_a_stranger(client: TestClient, method: str, path: str) -> None:
    response = getattr(client, method)(path)

    assert response.status_code == 401, path
    assert response.json()["error"]["code"] == "unauthorised"


def test_a_forged_cookie_is_rejected(client: TestClient) -> None:
    client.cookies.set("vault151_admin", "not.a.real.token")

    assert client.get("/api/admin/session").status_code == 401


def test_a_token_signed_with_another_secret_is_rejected(
    client: TestClient, admin_settings: Settings
) -> None:
    """Proves the signature is actually checked, not just the shape."""
    forged = jwt.encode(
        {"sub": "seller", "exp": 9_999_999_999},
        "a-different-secret-that-is-also-32-chars-long",
        algorithm="HS256",
    )
    client.cookies.set("vault151_admin", forged)

    assert client.get("/api/admin/session").status_code == 401


# --- signing in -----------------------------------------------------------------


def test_the_right_password_sets_an_httponly_cookie(client: TestClient) -> None:
    response = sign_in(client)

    assert response.status_code == 200
    assert response.json()["username"] == "seller"
    cookie = response.headers["set-cookie"]
    # httpOnly is what stops page scripts reading the session.
    assert "httponly" in cookie.lower()
    assert "samesite=lax" in cookie.lower()


def test_signing_in_opens_the_admin_area(client: TestClient) -> None:
    sign_in(client)

    assert client.get("/api/admin/session").status_code == 200


def test_signing_out_closes_it_again(client: TestClient) -> None:
    sign_in(client)
    client.post("/api/admin/logout")

    assert client.get("/api/admin/session").status_code == 401


def test_a_wrong_password_is_refused(client: TestClient) -> None:
    response = sign_in(client, "wrong")

    assert response.status_code == 401
    assert client.get("/api/admin/session").status_code == 401


def test_an_unknown_username_says_the_same_thing_as_a_wrong_password(
    client: TestClient,
) -> None:
    """Different messages would let someone discover whether a username exists."""
    wrong_user = client.post("/api/admin/login", json={"username": "nobody", "password": PASSWORD})
    wrong_password = sign_in(client, "wrong")

    assert wrong_user.status_code == wrong_password.status_code == 401
    assert wrong_user.json() == wrong_password.json()


def test_repeated_failures_lock_the_address_out(client: TestClient) -> None:
    for _ in range(5):
        sign_in(client, "wrong")

    locked = sign_in(client, "wrong")
    assert locked.status_code == 429
    assert locked.json()["error"]["code"] == "too_many_attempts"

    # The lock holds even once the password is right: that is the point.
    assert sign_in(client).status_code == 429


def test_the_counter_resets_after_a_success(client: TestClient) -> None:
    sign_in(client, "wrong")
    sign_in(client, "wrong")
    assert sign_in(client).status_code == 200

    for _ in range(4):
        sign_in(client, "wrong")
    # Four more failures is still under the limit, because the success cleared it.
    assert sign_in(client).status_code == 200
