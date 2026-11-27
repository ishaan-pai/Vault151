"""Application error types and the handlers that turn them into responses.

Rules this enforces:
  * errors are never swallowed - everything unexpected is logged with a stack trace;
  * a response never leaks internals or secrets outside development.

The error body shape is deliberately minimal here. The catalogue API step settles the
final contract, at which point this is the single place that changes.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import Settings

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for errors the application raises deliberately."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class DatabaseUnavailableError(AppError):
    """The connection pool could not provide a usable connection."""

    status_code = 503
    code = "database_unavailable"


class NotFoundError(AppError):
    """The requested resource does not exist, or is not visible to this caller."""

    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    """The request was valid but the world has moved on.

    Someone else bought the card, the reservation lapsed, or the order is already
    in a state that forbids what was asked. Not the caller's fault, so it is not a
    400; the resource exists, so it is not a 404.
    """

    status_code = 409
    code = "conflict"


def _body(code: str, message: str, details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if details:
        error["details"] = details
    return {"error": error}


def register_error_handlers(app: FastAPI, settings: Settings) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        # Expected failures: log at warning, and the message is safe to return
        # because we wrote it.
        logger.warning("%s: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(exc.code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Reshape FastAPI's default {"detail": [...]} into the one error envelope.

        Without this the frontend would need two error handlers: one for our errors
        and one for 422s. The per-field detail is preserved, minus the raw input,
        which can echo back whatever the caller sent.
        """
        details = [
            {
                "field": ".".join(str(part) for part in error["loc"][1:]),
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_body("invalid_request", "The request parameters are invalid.", details),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Unexpected failures: full stack trace to the log, nothing to the client
        # in production. In development the message is included, because a developer
        # staring at a 500 needs to know what broke.
        logger.exception("unhandled error on %s %s", request.method, request.url.path)
        message = (
            f"{type(exc).__name__}: {exc}" if settings.is_dev else "An unexpected error occurred."
        )
        return JSONResponse(status_code=500, content=_body("internal_error", message))
