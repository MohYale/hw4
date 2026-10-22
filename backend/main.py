"""Campus Customs API.

From the backend folder:
    uvicorn main:app --reload --port 8000
"""

import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import run_chat
from models import ChatReply, ChatTurn, TranscriptMessage
from passwords import hash_password, verify_password
from tools import load_transcript, open_page, save_chat_exchange, signed_in_shopper, turns_from_transcript

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "campus_customs.db"
PRODUCTS_DIR = ROOT / "data" / "products"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

app = FastAPI(title="Campus Customs")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


def connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return []


def product_dict(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json_list(row["colors"]),
        "search_tags": json_list(row["search_tags"]),
        "image_file_path": row["image_file_path"].replace("\\", "/"),
        "price": row["price"],
    }


class AccountBody(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str


class LoginBody(BaseModel):
    email: str
    password: str
    size: str = ""


class ForgotBody(BaseModel):
    email: str


class ResetBody(BaseModel):
    token: str
    password: str
    confirm_password: str


class OrderBody(BaseModel):
    id: int
    email: str
    product_id: str
    size: str
    color: str


class ShipBody(BaseModel):
    id: int
    email: str


class ChatShopperBody(BaseModel):
    id: int
    email: str


class ChatPageBody(BaseModel):
    path: str = ""
    product_id: str = ""


class ChatRequest(BaseModel):
    message: str
    history: list[ChatTurn] = []
    shopper: ChatShopperBody | None = None
    page: ChatPageBody | None = None


class HistoryRequest(BaseModel):
    id: int
    email: str


class HistoryResponse(BaseModel):
    messages: list[TranscriptMessage]


def clean_email(email: str) -> str:
    cleaned = email.strip().lower()
    if "@" not in cleaned or cleaned.startswith("@") or cleaned.endswith("@"):
        raise HTTPException(status_code=400, detail="Enter a valid email.")
    return cleaned


def public_user(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "preferred_size": row["preferred_size"] or "",
    }


def ensure_shop_tables() -> None:
    """Add the size column and the tables for reset links, orders, and shop emails."""
    connection = connect()
    try:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
        if "preferred_size" not in columns:
            connection.execute("ALTER TABLE users ADD COLUMN preferred_size TEXT")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                size TEXT NOT NULL,
                color TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'placed',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                shipped_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS outbound_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_id INTEGER,
                to_email TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                kind TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def utc_stamp(moment: datetime | None = None) -> str:
    current = moment or datetime.now(timezone.utc)
    return current.strftime("%Y-%m-%d %H:%M:%S")


def store_email(
    connection: sqlite3.Connection,
    user_id: int | None,
    order_id: int | None,
    to_email: str,
    subject: str,
    body: str,
    kind: str,
) -> None:
    connection.execute(
        """
        INSERT INTO outbound_emails (user_id, order_id, to_email, subject, body, kind)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, order_id, to_email, subject, body, kind),
    )


def size_key(size: str) -> int:
    try:
        return SIZE_ORDER.index(size)
    except ValueError:
        return len(SIZE_ORDER)


ensure_shop_tables()


@app.get("/api/products")
def list_products(size: str = "") -> list[dict]:
    chosen = size.strip().upper()
    if chosen and chosen not in SIZE_ORDER:
        raise HTTPException(status_code=400, detail="Choose a size from XS to XXL.")
    connection = connect()
    try:
        if chosen:
            rows = connection.execute(
                """
                SELECT product_id, name, garment_type, description, colors,
                       search_tags, image_file_path, price
                FROM catalogue
                WHERE product_id IN (
                    SELECT product_id FROM inventory
                    WHERE size = ? AND quantity > 0
                )
                ORDER BY name
                """,
                (chosen,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT product_id, name, garment_type, description, colors,
                       search_tags, image_file_path, price
                FROM catalogue
                ORDER BY name
                """
            ).fetchall()
    finally:
        connection.close()
    return [product_dict(row) for row in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    connection = connect()
    try:
        row = connection.execute(
            """
            SELECT product_id, name, garment_type, description, colors,
                   search_tags, image_file_path, price
            FROM catalogue
            WHERE product_id = ?
            """,
            (product_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
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
    product = product_dict(row)
    product["sizes"] = [
        {"size": stock["size"], "quantity": stock["quantity"]}
        for stock in sorted(stock_rows, key=lambda stock: size_key(stock["size"]))
    ]
    return product


@app.post("/api/account")
def create_account(body: AccountBody) -> dict:
    first_name = body.first_name.strip()
    last_name = body.last_name.strip()
    email = clean_email(body.email)
    if not first_name or not last_name:
        raise HTTPException(status_code=400, detail="Enter your first and last name.")
    if body.password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Those passwords do not match.")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Use at least 8 characters.")

    connection = connect()
    try:
        existing = connection.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="An account with that email already exists.",
            )
        cursor = connection.execute(
            """
            INSERT INTO users (name, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                f"{first_name} {last_name}",
                email,
                hash_password(body.password),
                first_name,
                last_name,
            ),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT id, name, email, first_name, last_name, preferred_size
            FROM users
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="An account with that email already exists.",
        ) from None
    finally:
        connection.close()
    return public_user(row)


@app.post("/api/login")
def login(body: LoginBody) -> dict:
    email = clean_email(body.email)
    size = body.size.strip().upper()
    if size and size not in SIZE_ORDER:
        raise HTTPException(status_code=400, detail="Choose a size from XS to XXL.")
    connection = connect()
    try:
        row = connection.execute(
            """
            SELECT id, name, email, password_hash, first_name, last_name, preferred_size
            FROM users
            WHERE email = ?
            """,
            (email,),
        ).fetchone()
        if row is None or not verify_password(body.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        if size:
            connection.execute(
                "UPDATE users SET preferred_size = ? WHERE id = ?",
                (size, row["id"]),
            )
            connection.commit()
            row = connection.execute(
                """
                SELECT id, name, email, first_name, last_name, preferred_size
                FROM users
                WHERE id = ?
                """,
                (row["id"],),
            ).fetchone()
    finally:
        connection.close()
    return public_user(row)


@app.post("/api/password/forgot")
def forgot_password(body: ForgotBody) -> dict:
    """Prepare a reset link. The message never includes the old password."""
    email = clean_email(body.email)
    connection = connect()
    try:
        row = connection.execute(
            "SELECT id, email FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="No account uses that email.")
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        expires = utc_stamp(datetime.now(timezone.utc) + timedelta(minutes=30))
        connection.execute(
            """
            INSERT INTO password_resets (user_id, token_hash, expires_at)
            VALUES (?, ?, ?)
            """,
            (row["id"], token_hash, expires),
        )
        reset_path = f"/reset-password?token={token}"
        subject = "Set a new Campus Customs password"
        message = (
            "Choose a new Campus Customs password with this link. "
            "It expires in 30 minutes. "
            "The shop cannot include your old password, because only a salted hash is stored.\n\n"
            f"http://127.0.0.1:5173{reset_path}"
        )
        store_email(connection, row["id"], None, row["email"], subject, message, "password_reset")
        connection.commit()
    finally:
        connection.close()
    return {
        "message": "A reset link is ready. It sets a new password and does not include the old one.",
        "reset_path": reset_path,
        "email_subject": subject,
        "email_body": message,
    }


@app.post("/api/password/reset")
def reset_password(body: ResetBody) -> dict:
    token = body.token.strip()
    if not token:
        raise HTTPException(status_code=400, detail="That reset link is missing.")
    if body.password != body.confirm_password:
        raise HTTPException(status_code=400, detail="Those passwords do not match.")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Use at least 8 characters.")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    connection = connect()
    try:
        row = connection.execute(
            """
            SELECT id, user_id, expires_at, used_at
            FROM password_resets
            WHERE token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
        if row is None or row["used_at"] or row["expires_at"] < utc_stamp():
            raise HTTPException(status_code=400, detail="That reset link is no longer valid.")
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(body.password), row["user_id"]),
        )
        connection.execute(
            "UPDATE password_resets SET used_at = ? WHERE id = ?",
            (utc_stamp(), row["id"]),
        )
        connection.commit()
    finally:
        connection.close()
    return {"message": "Your password is updated. Log in with the new one."}


@app.post("/api/orders")
def place_order(body: OrderBody) -> dict:
    """Buy one item if that size still has quantity and the color is on the product."""
    shopper = signed_in_shopper(body.id, body.email)
    if shopper is None:
        raise HTTPException(status_code=401, detail="Log in again to buy this item.")
    size = body.size.strip().upper()
    color = body.color.strip()
    if size not in SIZE_ORDER:
        raise HTTPException(status_code=400, detail="Choose a size from XS to XXL.")
    if not color:
        raise HTTPException(status_code=400, detail="Choose a color.")
    connection = connect()
    try:
        product = connection.execute(
            """
            SELECT product_id, name, colors
            FROM catalogue
            WHERE product_id = ?
            """,
            (body.product_id.strip(),),
        ).fetchone()
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        offered = {item.lower() for item in json_list(product["colors"])}
        if color.lower() not in offered:
            raise HTTPException(
                status_code=400,
                detail="That color is not offered on this item.",
            )
        connection.execute("BEGIN IMMEDIATE")
        updated = connection.execute(
            """
            UPDATE inventory
            SET quantity = quantity - 1
            WHERE product_id = ? AND size = ? AND quantity > 0
            """,
            (product["product_id"], size),
        )
        if updated.rowcount != 1:
            connection.rollback()
            raise HTTPException(status_code=409, detail="That size is sold out.")
        cursor = connection.execute(
            """
            INSERT INTO orders (user_id, product_id, product_name, size, color)
            VALUES (?, ?, ?, ?, ?)
            """,
            (shopper.user_id, product["product_id"], product["name"], size, color),
        )
        remaining = connection.execute(
            """
            SELECT quantity FROM inventory
            WHERE product_id = ? AND size = ?
            """,
            (product["product_id"], size),
        ).fetchone()
        connection.commit()
    except HTTPException:
        raise
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    return {
        "id": cursor.lastrowid,
        "product_id": product["product_id"],
        "product_name": product["name"],
        "size": size,
        "color": color,
        "status": "placed",
        "remaining": remaining["quantity"],
    }


@app.post("/api/orders/{order_id}/ship")
def ship_order(order_id: int, body: ShipBody) -> dict:
    """Mark an order shipped and record the email the shopper receives."""
    shopper = signed_in_shopper(body.id, body.email)
    if shopper is None:
        raise HTTPException(status_code=401, detail="Log in again to see this order.")
    connection = connect()
    try:
        order = connection.execute(
            """
            SELECT id, user_id, product_name, size, color, status
            FROM orders
            WHERE id = ?
            """,
            (order_id,),
        ).fetchone()
        if order is None or order["user_id"] != shopper.user_id:
            raise HTTPException(status_code=404, detail="Order not found")
        existing = connection.execute(
            """
            SELECT subject, body FROM outbound_emails
            WHERE order_id = ? AND kind = 'shipped'
            """,
            (order_id,),
        ).fetchone()
        if order["status"] == "shipped" and existing is not None:
            subject = existing["subject"]
            message = existing["body"]
        else:
            connection.execute(
                """
                UPDATE orders
                SET status = 'shipped', shipped_at = ?
                WHERE id = ?
                """,
                (utc_stamp(), order_id),
            )
            subject = f"Your {order['product_name']} has shipped"
            message = (
                f"Your Campus Customs order {order_id} has shipped.\n"
                f"{order['product_name']}, size {order['size']}, color {order['color']}.\n"
                "It is on its way."
            )
            store_email(
                connection,
                shopper.user_id,
                order_id,
                shopper.email,
                subject,
                message,
                "shipped",
            )
            connection.commit()
    finally:
        connection.close()
    return {
        "id": order_id,
        "status": "shipped",
        "email_subject": subject,
        "email_body": message,
    }


@app.post("/api/chat/history", response_model=HistoryResponse)
def chat_history(body: HistoryRequest) -> HistoryResponse:
    shopper = signed_in_shopper(body.id, body.email)
    if shopper is None:
        raise HTTPException(status_code=401, detail="Log in again to see your chat.")
    return HistoryResponse(messages=load_transcript(shopper.user_id))


@app.post("/api/chat", response_model=ChatReply)
async def chat(body: ChatRequest) -> ChatReply:
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Enter a message.")
    if len(message) > 2000:
        raise HTTPException(status_code=400, detail="That message is too long.")
    page_body = body.page or ChatPageBody()
    page = open_page(page_body.path, page_body.product_id)
    shopper = None
    history = body.history[-8:]
    if body.shopper is not None:
        shopper = signed_in_shopper(body.shopper.id, body.shopper.email)
        if shopper is None:
            raise HTTPException(status_code=401, detail="Log in again to save this chat.")
        history = turns_from_transcript(load_transcript(shopper.user_id))
    try:
        reply = await run_chat(message, history, shopper, page)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        print(f"Chat failed: {exc}", flush=True)
        raise HTTPException(
            status_code=502,
            detail="The shop assistant could not answer just now.",
        ) from exc
    if shopper is not None:
        save_chat_exchange(shopper.user_id, message, reply)
    return reply


app.mount(
    "/products",
    StaticFiles(directory=PRODUCTS_DIR),
    name="products",
)
