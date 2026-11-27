"""The stand-in provider used until Stripe test mode is wired in."""

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from .base import PaymentResult

logger = logging.getLogger(__name__)


class MockPaymentProvider:
    """Accepts every payment immediately and invents a reference.

    Deliberately boring: no artificial delay, no random failures. A test that needs a
    decline can use a provider stub that raises instead.
    """

    name = "mock"

    def charge(self, *, order_ref: str, amount: Decimal, currency: str) -> PaymentResult:
        reference = f"mock_{uuid.uuid4().hex[:24]}"
        logger.info(
            "mock payment accepted",
            extra={"order_ref": order_ref, "amount": str(amount), "currency": currency},
        )
        return PaymentResult(reference=reference, paid_at=datetime.now(UTC))
