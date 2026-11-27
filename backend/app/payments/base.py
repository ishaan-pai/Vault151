"""The payment boundary.

Checkout never names a payment company. It calls charge() on whatever provider is
configured, and stores what comes back. Adding Stripe test mode later means one new
class implementing this protocol plus a webhook route: no schema change, and no
change to order logic, because payment.method already carries the provider name and
payment.paymentreference already carries the provider's own transaction id.
"""

from datetime import datetime
from decimal import Decimal
from typing import NamedTuple, Protocol


class PaymentResult(NamedTuple):
    """What a provider gives back once money has changed hands."""

    reference: str
    """The provider's transaction id. Goes into payment.paymentreference."""

    paid_at: datetime
    """When the provider says it was paid, not when we recorded it."""


class PaymentFailedError(Exception):
    """The provider declined. Distinct from the provider being unreachable."""


class PaymentProvider(Protocol):
    name: str
    """Stored in payment.method, so a receipt says how it was paid."""

    def charge(self, *, order_ref: str, amount: Decimal, currency: str) -> PaymentResult:
        """Take payment for one order.

        order_ref is the guest-facing publicref, never the internal order id: it is
        what a provider dashboard should show. Raises PaymentFailedError if declined.
        """
        ...
