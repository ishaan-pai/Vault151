"""Application factory.

Run locally with:

    uv run uvicorn app.main:create_app --factory --reload

There is deliberately no module-level ``app = create_app()``: that would make importing
this module require a valid environment, so neither a test nor a tool could import it
without a configured database.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import api_router
from .config import Settings, get_settings
from .db import Database
from .errors import register_error_handlers
from .logging_setup import configure_logging
from .payments import MockPaymentProvider
from .security import LoginThrottle

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = Database(settings)
        database.connect()
        app.state.database = database
        logger.info("backend started", extra={"app_env": settings.app_env})
        try:
            yield
        finally:
            database.close()

    app = FastAPI(
        title="Card Shop API",
        version="0.1.0",
        lifespan=lifespan,
        # The interactive docs stay on in development only; whether they are exposed
        # in production is a deployment decision taken later.
        docs_url="/docs" if settings.is_dev else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.is_dev else None,
    )

    app.state.settings = settings
    # One provider for the process. Stripe test mode later means constructing a
    # different class here; nothing else in the application changes.
    app.state.payments = MockPaymentProvider()
    # In-memory, so it resets on restart: a speed bump against password guessing,
    # not a security boundary.
    app.state.login_throttle = LoginThrottle()

    # The browser calls the API from a different origin in development (Vite on
    # another port) and may do so in production depending on how it is served.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    register_error_handlers(app, settings)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app
