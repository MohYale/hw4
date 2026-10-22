"""Structured types for the Campus Customs shop assistant."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SizeStock(BaseModel):
    size: str
    quantity: int = Field(description="How many of this size are in inventory.")
    in_stock: bool = Field(description="False when quantity is 0. Say that size is out of stock.")


class ProductMatch(BaseModel):
    """One catalogue row the products page can render as a card."""

    product_id: str
    name: str
    garment_type: str
    price: float = Field(description="The price column from the catalogue.")
    short_description: str = Field(description="A short line from the catalogue description.")
    image_file_path: str = Field(description="Catalogue photo path, such as products/example.jpg.")


class ProductInfo(BaseModel):
    """One catalogue row: the description and the price."""

    found: bool
    product_id: str
    name: str = ""
    garment_type: str = ""
    description: str = ""
    price: float | None = None
    colors: list[str] = Field(default_factory=list)
    image_file_path: str = ""


class StockLookup(BaseModel):
    """Inventory for one product. Quantities come from the inventory table."""

    found: bool
    product_id: str
    name: str = ""
    sizes: list[SizeStock] = Field(default_factory=list)
    asked_size: str = ""
    asked_size_known: bool | None = None
    asked_size_quantity: int | None = None
    asked_size_in_stock: bool | None = None


class ProductCard(BaseModel):
    """One catalogue item the chat can show."""

    product_id: str
    name: str
    garment_type: str
    price: float
    description: str
    image_file_path: str = Field(description="Catalogue photo path, such as products/example.jpg.")
    sizes: list[SizeStock] = Field(default_factory=list)


class ChatReply(BaseModel):
    """What the shop assistant sends back to the website."""

    reply: str = Field(description="The message shown in the chat panel.")
    products: list[ProductCard] = Field(
        default_factory=list,
        description="Product cards copied from tool results. Empty when no product was looked up.",
    )
    matches: list[ProductMatch] = Field(
        default_factory=list,
        description=(
            "Catalogue rows from search_products. The website renders these "
            "as product cards. Empty when this turn did not search."
        ),
    )


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class CustomerProfile(BaseModel):
    """The signed-in shopper. A guest has logged_in false and empty name and email."""

    logged_in: bool
    name: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""


class PageView(BaseModel):
    """The page open in the browser. on_product is true only on one item's page."""

    on_product: bool
    path: str = ""
    product_id: str = ""
    name: str = ""
    garment_type: str = ""
    description: str = ""
    colors: list[str] = Field(default_factory=list)
    price: float | None = None
    image_file_path: str = ""


class TranscriptMessage(BaseModel):
    """One stored chat row, ready to show again in the widget."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
