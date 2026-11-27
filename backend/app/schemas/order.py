"""Request and response models for checkout and order lookup."""

from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field

from .catalogue import CamelModel

ShippingCountry = Literal["CA", "US"]


class ShippingAddress(CamelModel):
    """Where the cards are posted. Mirrors the address columns on salesorder."""

    recipient_name: str = Field(min_length=1, max_length=120)
    street: str = Field(min_length=1, max_length=200)
    city: str = Field(min_length=1, max_length=100)
    province: str | None = Field(default=None, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: ShippingCountry


class CreateOrderRequest(CamelModel):
    """A guest checkout. No account, so the email is the identity."""

    email: EmailStr
    display_name: str = Field(min_length=1, max_length=100)
    # No maximum: every line is one physical card and the shop holds a handful, so a
    # cart cannot exceed inventory. Duplicates are rejected rather than deduplicated,
    # since asking for the same unique card twice is a mistake worth reporting.
    listing_ids: list[int] = Field(min_length=1)
    shipping_address: ShippingAddress


class OrderLineItem(CamelModel):
    line_no: int
    listing_id: int
    card_name: str
    card_language: str
    variant: str
    card_condition: str
    agreed_price: str


class PaymentSummary(CamelModel):
    paid_at: datetime
    amount: str
    method: str
    reference: str


class OrderSummary(CamelModel):
    """Everything a guest sees about their order, before or after paying."""

    public_ref: str
    status: str
    placed_at: datetime
    expires_at: datetime | None
    """When an unpaid reservation lapses. Null once the order is no longer awaiting payment."""

    items: list[OrderLineItem]
    subtotal: str
    shipping_fee: str
    total: str
    currency: str
    shipping_address: ShippingAddress
    email: str
    payment: PaymentSummary | None


class ListingUnavailable(CamelModel):
    listing_id: int
    reason: str
