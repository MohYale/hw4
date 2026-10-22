"""Campus Customs shop assistant.

The system prompt is backend/prompts/prompt.md.
The model name comes from OPENAI_MODEL, or gpt-4o-mini when that is unset.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent, UsageLimits
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from audit import append_event, audited
from models import ChatReply, ChatTurn, ProductCard
from tools import (
    OpenPage,
    ShopDeps,
    SignedInShopper,
    current_customer,
    current_page,
    product_info,
    product_stock,
    search_products,
)

HERE = Path(__file__).resolve().parent
PROMPT_PATH = HERE / "prompts" / "prompt.md"
ROOT = HERE.parent

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

LOOP_SECONDS = 90
REQUEST_LIMIT = 12
TOOL_CALL_LIMIT = 10

_model: OpenAIChatModel | None = None
_agent: Agent[ShopDeps, ChatReply] | None = None


async def run_chat(
    message: str,
    history: list[ChatTurn],
    shopper: SignedInShopper | None = None,
    page: OpenPage | None = None,
) -> ChatReply:
    """Answer one shopper message. Product cards come from the tools, not from a guess."""
    deps = ShopDeps(shopper=shopper, page=page)
    question = message.strip()
    try:
        result = await asyncio.wait_for(
            get_agent().run(
                question,
                message_history=_history(history),
                deps=deps,
                instructions=_turn_context(deps),
                usage_limits=UsageLimits(
                    request_limit=REQUEST_LIMIT,
                    tool_calls_limit=TOOL_CALL_LIMIT,
                ),
            ),
            timeout=LOOP_SECONDS,
        )
    except TimeoutError:
        reply = ChatReply(
            reply=(
                "I have been trying for 90 seconds, so I am stopping. "
                "Ask again about one garment."
            )
        )
        append_event("loop", question, reply.reply, "stopped after 90 seconds")
        return reply
    except UsageLimitExceeded:
        reply = ChatReply(
            reply=(
                "I hit the lookup limit for this question, so I am stopping. "
                "Ask again about one garment."
            )
        )
        append_event("loop", question, reply.reply, "usage limit")
        return reply
    except Exception as exc:
        append_event("loop", question, type(exc).__name__, "error")
        raise
    reply = result.output
    reply.products = _cards_from_tools(reply.products, deps)
    reply.matches = list(deps.matches)
    append_event("loop", question, reply.reply, "completed")
    return reply


def get_agent() -> Agent[ShopDeps, ChatReply]:
    global _agent
    if _agent is None:
        _agent = Agent(
            build_model(),
            name="campus-customs-shop",
            instructions=PROMPT_PATH.read_text(encoding="utf-8"),
            deps_type=ShopDeps,
            output_type=ChatReply,
            tools=[
                audited(current_customer),
                audited(current_page),
                audited(search_products),
                audited(product_info),
                audited(product_stock),
            ],
        )
    return _agent


def build_model() -> OpenAIChatModel:
    global _model
    if _model is None:
        _load_env()
        model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        portkey_key = os.getenv("PORTKEY_API_KEY")
        if portkey_key:
            from openai import AsyncOpenAI

            headers: dict[str, str] = {}
            provider_name = os.getenv("PORTKEY_PROVIDER")
            if provider_name:
                headers["x-portkey-provider"] = provider_name
            client = AsyncOpenAI(
                api_key=portkey_key,
                base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
                default_headers=headers or None,
                timeout=60,
            )
            _model = OpenAIChatModel(model_name, provider=OpenAIProvider(openai_client=client))
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "No API key found. Set OPENAI_API_KEY or PORTKEY_API_KEY in a .env file."
                )
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=api_key, timeout=60)
            _model = OpenAIChatModel(model_name, provider=OpenAIProvider(openai_client=client))
    return _model


def _turn_context(deps: ShopDeps) -> str:
    """Page and account facts for this turn. The shopper's own words stay the message."""
    lines = [
        "Call current_customer before you greet the shopper by name or say who is signed in. "
        "Do not guess a name or an email. A guest has logged_in false."
    ]
    page = deps.page
    if page is not None and page.product_id:
        colors = ", ".join(page.colors) if page.colors else "none listed"
        lines.append(
            "The shopper is on a product page. "
            f"product_id: {page.product_id}. "
            f"name: {page.name}. "
            f"garment_type: {page.garment_type}. "
            f"colors: {colors}. "
            f"catalogue price: {page.price}. "
            "If they say this, it, or this one, they mean this product. "
            "Call current_page to read the page again. "
            "Use this product_id with product_info and product_stock. "
            "If they ask for a color that is not in colors, say this item does not come in that color."
        )
    else:
        path = page.path if page is not None and page.path else "a page that is not one product"
        lines.append(
            f"The shopper is on {path}. They are not on a single product page, "
            "so this or it does not name an item until they name one or open a product."
        )
    return " ".join(lines)


def _history(turns: list[ChatTurn]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for turn in turns[-8:]:
        text = turn.content.strip()
        if not text:
            continue
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=text)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=text)]))
    return messages


def _cards_from_tools(chosen: list[ProductCard], deps: ShopDeps) -> list[ProductCard]:
    if chosen:
        cards = [deps.cards[card.product_id] for card in chosen if card.product_id in deps.cards]
        if cards:
            return cards
    return list(deps.cards.values())[:3]


def _load_env() -> None:
    for path in (
        HERE / ".env",
        HERE / "API_key.env",
        ROOT / ".env",
        ROOT / "API_key.env",
        ROOT.parent / ".env",
        ROOT.parent / "API_key.env",
        ROOT.parent / "portkey_api_key.env",
        ROOT.parent / "lecture_6" / ".env",
        ROOT.parent / "lecture_6" / "API_key.env",
        ROOT.parent / "Lecture_5" / ".env",
    ):
        if path.is_file():
            load_dotenv(path, override=False)
