"""Typed application settings, loaded from the environment.

Nothing in the application reads os.environ directly: every value arrives here, is
validated once, and is passed around as a typed object. The password is a SecretStr so
that logging a Settings object cannot leak it.
"""

from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration for one running instance of the backend."""

    model_config = SettingsConfigDict(
        # backend/.env if present, else the repo-root .env, so running uvicorn from
        # backend/ picks up the same file docker compose uses. Inside the container
        # neither exists and the values come from the environment.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_env: Literal["dev", "prod"] = "dev"
    log_level: str = "INFO"
    api_prefix: str = "/api"

    # --- Database ---
    # APP_USER / APP_USER_PASSWORD have no defaults on purpose: the process should
    # refuse to start rather than fall back to a guess.
    app_user: str
    app_user_password: SecretStr
    db_host: str = "localhost"
    db_port: int = 1521
    db_service: str = "FREEPDB1"

    # --- Seller admin ---
    # One seller, so no admin table: the username and an argon2id hash of the
    # password come from the environment. Generate the hash with
    # `uv run python scripts/hash_password.py`.
    admin_username: str = "seller"
    admin_password_hash: SecretStr = SecretStr("")
    # Signs the session cookie. HS256 wants at least 32 bytes; a short or empty
    # secret can be guessed or brute-forced, which would let anyone forge a login.
    admin_jwt_secret: SecretStr = SecretStr("")
    admin_session_hours: int = Field(default=12, ge=1, le=168)

    # --- Card photos ---
    media_dir: str = "/srv/media"
    media_url_prefix: str = "/media"
    max_upload_bytes: int = Field(default=5_000_000, ge=1)

    # --- Checkout ---
    # How long an unpaid order holds its cards. There is no expiry column: expiry is
    # placedat plus this window, evaluated whenever someone looks.
    reservation_minutes: int = Field(default=30, ge=1, le=1440)

    # Flat rates in CAD. A country absent from this map is one we do not ship to,
    # so adding a destination is configuration rather than a code change.
    shipping_fee_ca: Decimal = Field(default=Decimal("15.00"), ge=0)
    shipping_fee_us: Decimal = Field(default=Decimal("30.00"), ge=0)

    # --- Catalogue ---
    default_page_size: int = Field(default=12, ge=1, le=48)
    featured_count: int = Field(default=4, ge=1, le=24)

    # --- Browser access ---
    # Comma-separated. Narrowed to the real domain by environment in production,
    # never by a code change.
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    db_pool_min: int = Field(default=1, ge=0)
    db_pool_max: int = Field(default=5, ge=1)
    db_pool_increment: int = Field(default=1, ge=0)

    @property
    def db_dsn(self) -> str:
        """Oracle easy-connect string, e.g. ``db:1521/FREEPDB1``."""
        return f"{self.db_host}:{self.db_port}/{self.db_service}"

    @field_validator("admin_jwt_secret")
    @classmethod
    def _secret_is_long_enough(cls, value: SecretStr) -> SecretStr:
        """Refuse to start rather than sign sessions with a guessable secret."""
        secret = value.get_secret_value()
        if len(secret) < 32:
            raise ValueError(
                "ADMIN_JWT_SECRET must be at least 32 characters. Generate one with: "
                'python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )
        return value

    @property
    def shipping_fees(self) -> dict[str, Decimal]:
        return {"CA": self.shipping_fee_ca, "US": self.shipping_fee_us}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_dev(self) -> bool:
        return self.app_env == "dev"


@lru_cache
def get_settings() -> Settings:
    """Settings are read once per process and cached."""
    return Settings()  # type: ignore[call-arg]  # values come from the environment
