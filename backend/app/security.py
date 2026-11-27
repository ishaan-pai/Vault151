"""Seller authentication.

There is one seller, so there is no admin table: the username and an argon2id hash
of the password come from the environment. A plaintext password is never stored
anywhere, and the hash is useless to anyone who reads it.

The session is a signed JWT in an httpOnly cookie. httpOnly means page JavaScript
cannot read it, so an injected script cannot steal the login; the browser simply
sends it back on each request.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from .config import Settings
from .errors import AppError

logger = logging.getLogger(__name__)

_hasher = PasswordHasher()

COOKIE_NAME = "vault151_admin"
ALGORITHM = "HS256"


class AuthError(AppError):
    """Wrong credentials, or no valid session."""

    status_code = 401
    code = "unauthorised"


class LockedOutError(AppError):
    """Too many failed attempts from one address."""

    status_code = 429
    code = "too_many_attempts"


def hash_password(password: str) -> str:
    """Used by scripts/hash_password.py to produce ADMIN_PASSWORD_HASH."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


@dataclass
class LoginThrottle:
    """Slows down password guessing from one address.

    Deliberately in memory: it resets when the process restarts and is per-process,
    which is honest about what it is - a speed bump, not a security boundary. With a
    single password it still turns thousands of guesses an hour into a handful.
    """

    max_attempts: int = 5
    lockout_seconds: int = 15 * 60
    _failures: dict[str, int] = field(default_factory=dict)
    _locked_until: dict[str, float] = field(default_factory=dict)

    def check(self, key: str) -> None:
        until = self._locked_until.get(key)
        if until and time.monotonic() < until:
            remaining = int(until - time.monotonic())
            raise LockedOutError(
                f"Too many failed sign-ins. Try again in {remaining // 60 + 1} minutes."
            )

    def record_failure(self, key: str) -> None:
        failures = self._failures.get(key, 0) + 1
        self._failures[key] = failures
        if failures >= self.max_attempts:
            self._locked_until[key] = time.monotonic() + self.lockout_seconds
            self._failures[key] = 0
            logger.warning("locked out after repeated failures", extra={"client": key})

    def record_success(self, key: str) -> None:
        self._failures.pop(key, None)
        self._locked_until.pop(key, None)


def issue_token(settings: Settings, subject: str) -> tuple[str, int]:
    """Return a signed token and its lifetime in seconds."""
    lifetime = timedelta(hours=settings.admin_session_hours)
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
    }
    token = jwt.encode(payload, settings.admin_jwt_secret.get_secret_value(), algorithm=ALGORITHM)
    return token, int(lifetime.total_seconds())


def read_token(settings: Settings, token: str) -> str:
    """The subject of a valid token, or AuthError if it is expired or forged."""
    try:
        payload = jwt.decode(
            token, settings.admin_jwt_secret.get_secret_value(), algorithms=[ALGORITHM]
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Your session has expired. Please sign in again.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Please sign in.") from exc
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise AuthError("Please sign in.")
    return subject
