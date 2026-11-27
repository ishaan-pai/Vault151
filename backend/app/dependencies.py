"""Shared FastAPI dependencies.

The pool and the settings live on ``app.state`` so a test can build the application
with a stand-in and never touch Oracle.
"""

from fastapi import Request

from .config import Settings
from .db import Database
from .payments import MockPaymentProvider, PaymentProvider
from .repositories.admin import AdminRepository
from .repositories.catalogue import CatalogueRepository
from .repositories.orders import OrderRepository
from .security import COOKIE_NAME, AuthError, read_token
from .services.admin import AdminService
from .services.catalogue import CatalogueService
from .services.checkout import CheckoutService
from .services.reports import ReportService


def get_database(request: Request) -> Database:
    database: Database = request.app.state.database
    return database


def get_settings_dependency(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_catalogue_service(request: Request) -> CatalogueService:
    """Wires repository to service. Both are cheap; the pool is the shared resource."""
    return CatalogueService(CatalogueRepository(get_database(request)))


def get_payment_provider(request: Request) -> PaymentProvider:
    """The configured provider. Swapping in Stripe later changes only this line."""
    provider: PaymentProvider = (
        getattr(request.app.state, "payments", None) or MockPaymentProvider()
    )
    return provider


def require_admin(request: Request) -> str:
    """Guards every admin route. Declared once on the router, not per endpoint."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise AuthError("Please sign in.")
    return read_token(get_settings_dependency(request), token)


def get_admin_service(request: Request) -> AdminService:
    return AdminService(
        get_database(request),
        AdminRepository(),
        get_settings_dependency(request),
    )


def get_report_service(request: Request) -> ReportService:
    return ReportService(get_database(request))


def get_checkout_service(request: Request) -> CheckoutService:
    return CheckoutService(
        get_database(request),
        OrderRepository(),
        get_payment_provider(request),
        get_settings_dependency(request),
    )
