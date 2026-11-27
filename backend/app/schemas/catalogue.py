"""Response models for the catalogue.

Python stays snake_case; the JSON contract is camelCase, produced by an alias generator
rather than by hand so the two can never drift. FastAPI serialises by alias.

Money is a string, not a number: prices are Oracle NUMBER(10,2), and a JSON number is a
float, where "663.00" can come back as 662.99999999. The currency travels beside it
instead of being assumed by the reader.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base for everything on the wire: snake_case in, camelCase out."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class GradingInfo(CamelModel):
    """Present only for slabbed cards; raw cards carry ``null``."""

    company: str
    grade: str
    certification_number: str


class ListingSummary(CamelModel):
    """One card as it appears in a catalogue grid or the feature strip."""

    listing_id: int
    card_name: str
    set_name: str
    collector_number: str
    variant: str
    rarity: str
    card_condition: str
    asking_price: str
    currency: str
    image_url: str | None
    listed_at: date
    grading: GradingInfo | None


class ListingDetail(ListingSummary):
    """Everything the card detail page shows."""

    copy_id: int
    set_id: int
    card_language: str
    description: str


class ListingPage(CamelModel):
    """A page of catalogue results, with enough to render "page 3 of 5"."""

    items: list[ListingSummary]
    page: int
    page_size: int
    total_items: int
    total_pages: int


class CardSetSummary(CamelModel):
    set_id: int
    set_name: str
    release_date: date


class FilterOptions(CamelModel):
    """The distinct values available in each catalogue filter."""

    rarities: list[str]
    variants: list[str]
    conditions: list[str]
