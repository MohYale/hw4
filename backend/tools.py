"""Catalogue, inventory, and shopper tools for the shop assistant.

Prices come from catalogue. Quantities come from inventory.
current_customer reads only the signed-in shopper's name and email.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from pydantic_ai import RunContext

from models import (
    ChatReply,
    ChatTurn,
    CustomerProfile,
    PageView,
    ProductCard,
    ProductInfo,
    ProductMatch,
    SizeStock,
    StockLookup,
    TranscriptMessage,
)

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "campus_customs.db"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
SEARCH_LIMIT = 24
STOP_WORDS = {
    "what",
    "which",
    "do",
    "you",
    "have",
    "the",
    "a",
    "an",
    "of",
    "for",
    "me",
    "show",
    "any",
    "there",
    "are",
    "is",
    "please",
    "can",
    "your",
    "our",
    "some",
    "with",
    "and",
    "or",
    "in",
    "on",
    "to",
    "it",
    "we",
}
WORD_FOLDS = {
    "sleeved": "sleeve",
    "sleeves": "sleeve",
    "shirts": "shirt",
    "tshirts": "tshirt",
    "tees": "tee",
    "hoodies": "hoodie",
    "crewnecks": "crewneck",
}
SIZE_ALIASES = {
    "XS": "XS",
    "EXTRA SMALL": "XS",
    "S": "S",
    "SMALL": "S",
    "M": "M",
    "MEDIUM": "M",
    "L": "L",
    "LARGE": "L",
    "XL": "XL",
    "EXTRA LARGE": "XL",
    "XXL": "XXL",
    "2XL": "XXL",
}


@dataclass
class SignedInShopper:
    user_id: int
    name: str
    email: str
    first_name: str
    last_name: str


@dataclass
class OpenPage:
    path: str = ""
    product_id: str = ""
    name: str = ""
    garment_type: str = ""
    description: str = ""
    colors: list[str] = field(default_factory=list)
    price: float | None = None
    image_file_path: str = ""


@dataclass
class ShopDeps:
    cards: dict[str, ProductCard] = field(default_factory=dict)
    sizes: dict[str, list[SizeStock]] = field(default_factory=dict)
    matches: list[ProductMatch] = field(default_factory=list)
    shopper: SignedInShopper | None = None
    page: OpenPage | None = None


def current_customer(ctx: RunContext[ShopDeps]) -> CustomerProfile:
    """Read the person signed in to this chat.

    Returns that shopper's name and email from the users table.
    logged_in is false for a guest, and name and email are then empty.
    This is only the person in this chat. It does not list other accounts
    and it does not return a password.
    """
    shopper = ctx.deps.shopper
    if shopper is None:
        return CustomerProfile(logged_in=False)
    return CustomerProfile(
        logged_in=True,
        name=shopper.name,
        email=shopper.email,
        first_name=shopper.first_name,
        last_name=shopper.last_name,
    )


def current_page(ctx: RunContext[ShopDeps]) -> PageView:
    """Read the page open on the website.

    When on_product is true, the shopper is on that item's page.
    product_id, name, garment_type, colors, and price are that catalogue row.
    Words such as "this" or "it" mean that item.
    When on_product is false, they are not on a single product page.
    """
    page = ctx.deps.page
    if page is None or not page.product_id:
        path = page.path if page is not None else ""
        return PageView(on_product=False, path=path)
    return PageView(
        on_product=True,
        path=page.path,
        product_id=page.product_id,
        name=page.name,
        garment_type=page.garment_type,
        description=page.description,
        colors=list(page.colors),
        price=page.price,
        image_file_path=page.image_file_path,
    )


def search_products(ctx: RunContext[ShopDeps], query: str) -> list[ProductMatch]:
    """Find catalogue products that match the shopper's words.

    query is words such as "long sleeved t shirts" or "navy hoodie".
    Returns matching catalogue rows with name, price, photo path, and a short description.
    Those rows are what the products page renders. Call product_info before you
    state one item's price in a sentence, and product_stock for quantities.
    """
    matches = _search(query)
    ctx.deps.matches = matches
    return matches


def product_info(ctx: RunContext[ShopDeps], product_id: str) -> ProductInfo:
    """Read one catalogue row: description, price, and colors.

    product_id is the catalogue id from search_products, such as "basic-hoodie-big-yale".
    price is the catalogue price. description is the catalogue description.
    found is false when that id is not in the catalogue.
    """
    info = _product_info(product_id)
    if info.found and info.price is not None:
        ctx.deps.cards[info.product_id] = ProductCard(
            product_id=info.product_id,
            name=info.name,
            garment_type=info.garment_type,
            price=info.price,
            description=info.description,
            image_file_path=info.image_file_path,
            sizes=ctx.deps.sizes.get(info.product_id, []),
        )
    return info


def product_stock(ctx: RunContext[ShopDeps], product_id: str, size: str = "") -> StockLookup:
    """Read how many of each size are in inventory.

    product_id is the catalogue id. size is optional, such as "M" or "large",
    when the shopper asked about one size.
    in_stock is false when quantity is 0. Say that size is out of stock.
    This tool does not return a price.
    """
    stock = _product_stock(product_id, size)
    if stock.found:
        ctx.deps.sizes[stock.product_id] = stock.sizes
        card = ctx.deps.cards.get(stock.product_id)
        if card is not None:
            card.sizes = stock.sizes
    return stock


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _search(query: str) -> list[ProductMatch]:
    words = [word for word in _fold(query) if word not in STOP_WORDS]
    if not words:
        return []
    connection = _connect()
    try:
        rows = connection.execute(
            """
            SELECT product_id, name, garment_type, description, colors,
                   search_tags, image_file_path, price
            FROM catalogue
            """
        ).fetchall()
    finally:
        connection.close()
    matched: list[tuple[int, ProductMatch]] = []
    for row in rows:
        blob_words = set(
            _fold(
                " ".join(
                    [
                        row["name"],
                        row["garment_type"],
                        row["description"],
                        row["colors"],
                        row["search_tags"],
                        row["product_id"],
                    ]
                )
            )
        )
        if not all(word in blob_words for word in words):
            continue
        name_words = set(_fold(row["name"]))
        score = sum(1 for word in words if word in name_words)
        description = " ".join(str(row["description"]).split())
        if len(description) > 140:
            description = description[:139].rstrip() + "…"
        matched.append(
            (
                score,
                ProductMatch(
                    product_id=row["product_id"],
                    name=row["name"],
                    garment_type=row["garment_type"],
                    price=float(row["price"]),
                    short_description=description,
                    image_file_path=str(row["image_file_path"]).replace("\\", "/"),
                ),
            )
        )
    matched.sort(key=lambda item: (-item[0], item[1].name))
    return [match for _, match in matched[:SEARCH_LIMIT]]


def _fold(text: str) -> list[str]:
    words: list[str] = []
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        word = WORD_FOLDS.get(word, word)
        if word.endswith("s") and len(word) > 4:
            word = word[:-1]
        if len(word) > 1:
            words.append(word)
    return words


def _product_info(product_id: str) -> ProductInfo:
    connection = _connect()
    try:
        row = connection.execute(
            """
            SELECT product_id, name, garment_type, description, colors,
                   image_file_path, price
            FROM catalogue
            WHERE product_id = ?
            """,
            (product_id.strip(),),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return ProductInfo(found=False, product_id=product_id.strip())
    description = " ".join(str(row["description"]).split())
    return ProductInfo(
        found=True,
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=description,
        price=float(row["price"]),
        colors=_json_list(row["colors"]),
        image_file_path=str(row["image_file_path"]).replace("\\", "/"),
    )


def _product_stock(product_id: str, size: str) -> StockLookup:
    product_id = product_id.strip()
    connection = _connect()
    try:
        name_row = connection.execute(
            "SELECT name FROM catalogue WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        if name_row is None:
            return StockLookup(found=False, product_id=product_id)
        stock_rows = connection.execute(
            """
            SELECT size, quantity
            FROM inventory
            WHERE product_id = ?
            """,
            (product_id,),
        ).fetchall()
    finally:
        connection.close()
    sizes = [
        SizeStock(
            size=stock["size"],
            quantity=int(stock["quantity"]),
            in_stock=int(stock["quantity"]) > 0,
        )
        for stock in sorted(stock_rows, key=lambda stock: _size_key(stock["size"]))
    ]
    lookup = StockLookup(
        found=True,
        product_id=product_id,
        name=name_row["name"],
        sizes=sizes,
    )
    asked = _canonical_size(size)
    if not asked:
        return lookup
    lookup.asked_size = asked
    match = next((item for item in sizes if item.size.upper() == asked), None)
    if match is None:
        lookup.asked_size_known = False
        return lookup
    lookup.asked_size_known = True
    lookup.asked_size_quantity = match.quantity
    lookup.asked_size_in_stock = match.in_stock
    return lookup


def _canonical_size(size: str) -> str:
    cleaned = " ".join(size.upper().split())
    if not cleaned:
        return ""
    return SIZE_ALIASES.get(cleaned, cleaned)


def _json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return []


def _size_key(size: str) -> int:
    try:
        return SIZE_ORDER.index(size)
    except ValueError:
        return len(SIZE_ORDER)


def signed_in_shopper(user_id: int, email: str) -> SignedInShopper | None:
    """Match a signed-in id and email to one users row. None when they do not match."""
    cleaned = email.strip().lower()
    if not cleaned:
        return None
    connection = _connect()
    try:
        row = connection.execute(
            """
            SELECT id, name, email, first_name, last_name
            FROM users
            WHERE id = ? AND lower(email) = ?
            """,
            (user_id, cleaned),
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return SignedInShopper(
        user_id=int(row["id"]),
        name=row["name"] or "",
        email=row["email"],
        first_name=row["first_name"] or "",
        last_name=row["last_name"] or "",
    )


def open_page(path: str, product_id: str) -> OpenPage:
    """Build the page the shopper is looking at. A product id is filled from catalogue."""
    page = OpenPage(path=path.strip()[:300], product_id=product_id.strip())
    if not page.product_id:
        return page
    info = _product_info(page.product_id)
    if not info.found or info.price is None:
        page.product_id = ""
        return page
    page.name = info.name
    page.garment_type = info.garment_type
    page.description = info.description
    page.colors = list(info.colors)
    page.price = info.price
    page.image_file_path = info.image_file_path
    return page


def load_transcript(user_id: int, limit: int = 80) -> list[TranscriptMessage]:
    """Read one shopper's chat_messages rows, oldest first."""
    connection = _connect()
    try:
        rows = connection.execute(
            """
            SELECT role, content, products_json
            FROM chat_messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    finally:
        connection.close()
    messages: list[TranscriptMessage] = []
    for row in reversed(rows):
        role = row["role"]
        if role not in ("user", "assistant"):
            continue
        content = str(row["content"]).strip()
        if not content:
            continue
        messages.append(
            TranscriptMessage(
                role=role,
                content=content,
                products=_products_from_json(row["products_json"]),
            )
        )
    return messages


def turns_from_transcript(messages: list[TranscriptMessage], limit: int = 8) -> list[ChatTurn]:
    """The latest stored turns, clipped to what ChatTurn accepts."""
    turns: list[ChatTurn] = []
    for message in messages:
        text = message.content.strip()
        if not text:
            continue
        turns.append(ChatTurn(role=message.role, content=text[:2000]))
    return turns[-limit:]


def save_chat_exchange(user_id: int, user_text: str, reply: ChatReply) -> None:
    """Store the shopper's message and the assistant reply for a signed-in account."""
    products = json.dumps([card.model_dump(mode="json") for card in reply.products])
    connection = _connect()
    try:
        connection.execute(
            """
            INSERT INTO chat_messages (user_id, role, content, products_json)
            VALUES (?, 'user', ?, NULL)
            """,
            (user_id, user_text),
        )
        connection.execute(
            """
            INSERT INTO chat_messages (user_id, role, content, products_json)
            VALUES (?, 'assistant', ?, ?)
            """,
            (user_id, reply.reply, products),
        )
        connection.commit()
    finally:
        connection.close()


def _products_from_json(raw: str | None) -> list[ProductCard]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    cards: list[ProductCard] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        product_id = str(item.get("product_id") or "").strip()
        if not product_id:
            continue
        try:
            price = float(item["price"])
        except (KeyError, TypeError, ValueError):
            continue
        sizes: list[SizeStock] = []
        raw_sizes = item.get("sizes") or item.get("inventory") or []
        if isinstance(raw_sizes, list):
            for stock in raw_sizes:
                if not isinstance(stock, dict) or "size" not in stock:
                    continue
                try:
                    quantity = int(stock.get("quantity") or 0)
                except (TypeError, ValueError):
                    quantity = 0
                sizes.append(
                    SizeStock(size=str(stock["size"]), quantity=quantity, in_stock=quantity > 0)
                )
        cards.append(
            ProductCard(
                product_id=product_id,
                name=str(item.get("name") or product_id),
                garment_type=str(item.get("garment_type") or ""),
                price=price,
                description=str(item.get("description") or ""),
                image_file_path=str(item.get("image_file_path") or "").replace("\\", "/"),
                sizes=sizes,
            )
        )
    return cards
