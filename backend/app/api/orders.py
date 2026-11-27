"""Checkout, payment and guest order lookup.

Sync `def` endpoints, so the blocking Oracle driver runs in FastAPI's threadpool and
each request's transaction stays on one connection for its whole life.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status

from ..dependencies import get_checkout_service
from ..schemas.order import CreateOrderRequest, OrderSummary
from ..services.checkout import CheckoutService

router = APIRouter(tags=["orders"])

PublicRef = Annotated[str, Path(min_length=8, max_length=32, pattern=r"^[0-9A-Fa-f]+$")]


@router.post(
    "/orders",
    response_model=OrderSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Place an order and reserve its cards",
    responses={
        404: {"description": "One of the listings does not exist."},
        409: {"description": "A card is no longer available, or we do not ship there."},
    },
)
def create_order(
    request: CreateOrderRequest,
    service: Annotated[CheckoutService, Depends(get_checkout_service)],
) -> OrderSummary:
    """Reserve the cards and create the order, in one transaction.

    Returns 409 rather than 400 when a card has gone: the request was valid, the
    world simply moved on between browsing and checking out.
    """
    return service.create_order(request)


@router.post(
    "/orders/{public_ref}/pay",
    response_model=OrderSummary,
    summary="Pay for an order",
    responses={
        404: {"description": "No order with that reference."},
        409: {"description": "The order cannot be paid in its current state."},
    },
)
def pay_order(
    public_ref: PublicRef,
    service: Annotated[CheckoutService, Depends(get_checkout_service)],
) -> OrderSummary:
    """Take payment and mark the cards sold.

    Safe to call twice: the second call finds the order already paid and returns the
    original payment rather than charging again.
    """
    return service.pay(public_ref)


@router.get(
    "/orders/{public_ref}",
    response_model=OrderSummary,
    summary="Look up a guest order",
    responses={404: {"description": "No order matches that reference and email."}},
)
def get_order(
    public_ref: PublicRef,
    email: Annotated[str, Query(min_length=3, max_length=254)],
    service: Annotated[CheckoutService, Depends(get_checkout_service)],
) -> OrderSummary:
    """Both the reference and the email must match.

    There are no accounts, so this pair is the whole of order security: the
    reference is random and unguessable, and the email is known to the buyer.
    """
    return service.find_order(public_ref, email)
