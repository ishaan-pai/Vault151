"""Request and response models for the seller's admin area."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from .catalogue import CamelModel

CardCondition = Literal["NearMint", "LightlyPlayed", "ModeratelyPlayed", "HeavilyPlayed", "Damaged"]


class LoginRequest(CamelModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class SessionInfo(CamelModel):
    username: str
    expires_in: int


class GradingInput(CamelModel):
    company: str = Field(min_length=1, max_length=60)
    grade: str = Field(min_length=1, max_length=20)
    certification_number: str = Field(min_length=1, max_length=80)


class NewCardRequest(CamelModel):
    """Add one physical card and list it, in a single step.

    The set and the printing are reused when they already exist, so adding a second
    copy of a card the shop has sold before does not duplicate either.
    """

    set_name: str = Field(min_length=1, max_length=120)
    set_release_date: date
    card_name: str = Field(min_length=1, max_length=120)
    collector_number: str = Field(min_length=1, max_length=20)
    card_language: str = Field(default="English", min_length=1, max_length=30)
    variant: str = Field(min_length=1, max_length=60)
    rarity: str = Field(min_length=1, max_length=40)
    card_condition: CardCondition
    description: str = Field(min_length=1, max_length=1000)
    asking_price: Decimal = Field(gt=0, decimal_places=2)
    grading: GradingInput | None = None


class UpdateListingRequest(CamelModel):
    """Only the price is editable; status has its own endpoints."""

    asking_price: Decimal = Field(gt=0, decimal_places=2)


class AdminListing(CamelModel):
    listing_id: int
    copy_id: int
    card_name: str
    set_name: str
    collector_number: str
    variant: str
    rarity: str
    card_condition: str
    description: str
    asking_price: str
    status: str
    listed_at: date
    image_url: str | None
    editable: bool
    deletable: bool


class ShipmentInput(CamelModel):
    carrier: str = Field(min_length=1, max_length=60)
    tracking_number: str = Field(min_length=1, max_length=100)


class ShipmentInfo(CamelModel):
    carrier: str
    tracking_number: str
    shipped_at: datetime
    delivered_at: datetime | None


class AdminOrderRow(CamelModel):
    public_ref: str
    status: str
    placed_at: datetime
    customer_name: str
    email: str
    card_count: int
    subtotal: str
    shipping_fee: str
    total: str
    shipment: ShipmentInfo | None
