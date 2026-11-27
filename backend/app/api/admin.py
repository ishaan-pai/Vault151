"""The seller's admin area.

Every route below `/api/admin` except sign-in depends on `require_admin`, so adding a
new admin endpoint cannot accidentally be public: the dependency is declared on the
router, not repeated per route.
"""

import logging
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Path, Query, Request, Response, UploadFile

from ..config import Settings
from ..dependencies import (
    get_admin_service,
    get_report_service,
    get_settings_dependency,
    require_admin,
)
from ..schemas.admin import (
    AdminListing,
    AdminOrderRow,
    LoginRequest,
    NewCardRequest,
    SessionInfo,
    ShipmentInfo,
    ShipmentInput,
    UpdateListingRequest,
)
from ..schemas.reports import Report, ReportSummary
from ..security import (
    COOKIE_NAME,
    AuthError,
    issue_token,
    verify_password,
)
from ..services.admin import STATUS_ACTIVE, STATUS_WITHDRAWN, AdminService
from ..services.reports import ReportKey, ReportService

logger = logging.getLogger(__name__)

PublicRef = Annotated[str, Path(min_length=8, max_length=32, pattern=r"^[0-9A-Fa-f]+$")]

# Sign-in and sign-out are open; everything else requires the cookie.
public_router = APIRouter(prefix="/admin", tags=["admin"])
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@public_router.post("/login", response_model=SessionInfo, summary="Sign in")
def login(
    credentials: LoginRequest,
    request: Request,
    response: Response,
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> SessionInfo:
    """Check the password and set an httpOnly session cookie.

    The same message is returned for an unknown username and a wrong password, so
    the response cannot be used to discover which half was right.
    """
    throttle = request.app.state.login_throttle
    client = request.client.host if request.client else "unknown"
    throttle.check(client)

    correct = credentials.username == settings.admin_username and verify_password(
        credentials.password, settings.admin_password_hash.get_secret_value()
    )
    if not correct:
        throttle.record_failure(client)
        logger.warning("failed admin sign-in", extra={"client": client})
        raise AuthError("Incorrect username or password.")

    throttle.record_success(client)
    token, lifetime = issue_token(settings, settings.admin_username)
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=lifetime,
        httponly=True,  # page scripts cannot read it, so it cannot be stolen by one
        samesite="lax",
        secure=not settings.is_dev,  # over HTTPS only, once deployed
        path="/",
    )
    return SessionInfo(username=settings.admin_username, expires_in=lifetime)


@public_router.post("/logout", summary="Sign out")
def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"signedOut": True}


@router.get("/session", response_model=SessionInfo, summary="Who am I")
def session(
    settings: Annotated[Settings, Depends(get_settings_dependency)],
) -> SessionInfo:
    """Lets the admin UI decide whether to show the sign-in page on load."""
    return SessionInfo(
        username=settings.admin_username, expires_in=settings.admin_session_hours * 3600
    )


# --- inventory ------------------------------------------------------------------


@router.post("/cards", response_model=AdminListing, status_code=201, summary="Add a card")
def add_card(
    request: NewCardRequest,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminListing:
    """Create the card and list it. Reuses the set and printing if they exist."""
    return service.add_card(request)


@router.get("/listings/{listing_id}", response_model=AdminListing)
def get_listing(
    listing_id: Annotated[int, Path(ge=1)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminListing:
    return service.get_listing(listing_id)


@router.patch("/listings/{listing_id}", response_model=AdminListing, summary="Change the price")
def update_listing(
    listing_id: Annotated[int, Path(ge=1)],
    body: UpdateListingRequest,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminListing:
    return service.set_price(listing_id, Decimal(body.asking_price))


@router.post(
    "/listings/{listing_id}/status",
    response_model=AdminListing,
    summary="Disable or re-enable a listing",
    responses={409: {"description": "The card is reserved or sold."}},
)
def set_listing_status(
    listing_id: Annotated[int, Path(ge=1)],
    status: Annotated[Literal["Active", "Withdrawn"], Query()],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> AdminListing:
    """Disabling is reversible and always available while a card is unsold."""
    return service.set_status(listing_id, STATUS_ACTIVE if status == "Active" else STATUS_WITHDRAWN)


@router.delete(
    "/listings/{listing_id}",
    status_code=204,
    summary="Delete a listing permanently",
    responses={409: {"description": "The card has been ordered; disable it instead."}},
)
def delete_listing(
    listing_id: Annotated[int, Path(ge=1)],
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> None:
    """Refused once the card appears on an order, to protect that order's history."""
    service.delete_listing(listing_id)


@router.post(
    "/listings/{listing_id}/image",
    response_model=AdminListing,
    summary="Attach or replace the card photo",
    responses={
        413: {"description": "The image is larger than the limit."},
        415: {"description": "Not a JPEG, PNG or WebP."},
    },
)
async def upload_image(
    listing_id: Annotated[int, Path(ge=1)],
    service: Annotated[AdminService, Depends(get_admin_service)],
    file: Annotated[UploadFile, File()],
) -> AdminListing:
    """Works at any point after listing, so photos can follow later.

    Async only because reading the upload stream is async; the database work behind
    it is the usual synchronous call.
    """
    content = await file.read()
    return service.attach_image(listing_id, content)


# --- reports --------------------------------------------------------------------


@router.get(
    "/reports",
    response_model=list[ReportSummary],
    summary="The available reports",
)
def list_reports(
    service: Annotated[ReportService, Depends(get_report_service)],
) -> list[ReportSummary]:
    return service.menu()


@router.get(
    "/reports/{key}",
    response_model=Report,
    summary="Run one report",
    responses={404: {"description": "No report by that name."}},
)
def run_report(
    key: ReportKey,
    service: Annotated[ReportService, Depends(get_report_service)],
    min_cards: Annotated[int, Query(alias="minCards", ge=1, le=50)] = 2,
) -> Report:
    """Returns the rows and the statement that produced them.

    The SQL travels with the result so the page can show its own workings, which is
    the point of these reports: they are where the graded query features appear in
    the running product.
    """
    return service.run(key, min_cards=min_cards)


# --- orders ---------------------------------------------------------------------


@router.get("/orders", response_model=list[AdminOrderRow], summary="All orders")
def list_orders(
    service: Annotated[AdminService, Depends(get_admin_service)],
    status: Annotated[str | None, Query(max_length=20)] = None,
) -> list[AdminOrderRow]:
    return service.orders(status)


@router.post(
    "/orders/{public_ref}/shipment",
    response_model=ShipmentInfo,
    status_code=201,
    summary="Record a dispatch",
    responses={409: {"description": "Unpaid, or already dispatched."}},
)
def record_shipment(
    public_ref: PublicRef,
    body: ShipmentInput,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> ShipmentInfo:
    return service.record_shipment(public_ref, body)


@router.post(
    "/orders/{public_ref}/delivered",
    response_model=ShipmentInfo,
    summary="Mark delivered",
    responses={409: {"description": "Not dispatched, or already delivered."}},
)
def mark_delivered(
    public_ref: PublicRef,
    service: Annotated[AdminService, Depends(get_admin_service)],
) -> ShipmentInfo:
    return service.mark_delivered(public_ref)
