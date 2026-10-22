"""Append-only log of one shop-agent loop.

output/audit_trail.json is a JSON list. New runs add records.
They do not replace the records already in the file.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "output" / "audit_trail.json"
LOCK_PATH = ROOT / "output" / "audit_trail.lock"
SHORT = 240


def append_event(tool: str, args: str, result: str, stop_reason: str) -> None:
    """Add one record. Existing records stay."""
    record = {
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": tool,
        "args": _clip(args),
        "result": _clip(result),
        "stop_reason": stop_reason,
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock = _lock()
    try:
        try:
            events = _read_events()
        except json.JSONDecodeError:
            print("audit file was not a JSON list; leaving it unchanged", flush=True)
            return
        events.append(record)
        AUDIT_PATH.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")
    finally:
        _unlock(lock)


def audited(fn):
    """Record a tool call, then return the tool's own result."""

    @wraps(fn)
    def wrapped(*args, **kwargs):
        tool_args = _short_args(args, kwargs)
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            append_event(fn.__name__, tool_args, f"error {type(exc).__name__}", "")
            raise
        append_event(fn.__name__, tool_args, _short_result(result), "")
        return result

    return wrapped


def _read_events() -> list[dict[str, str]]:
    if not AUDIT_PATH.is_file():
        return []
    raw = AUDIT_PATH.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        raise json.JSONDecodeError("audit file is not a list", raw, 0)
    return parsed


def _lock() -> int:
    for _ in range(50):
        try:
            return os.open(str(LOCK_PATH), os.O_CREAT | os.O_EXCL | os.O_RDWR)
        except FileExistsError:
            import time

            time.sleep(0.05)
    return os.open(str(LOCK_PATH), os.O_CREAT | os.O_RDWR)


def _unlock(handle: int) -> None:
    os.close(handle)
    try:
        LOCK_PATH.unlink()
    except OSError:
        pass


def _short_args(args: tuple, kwargs: dict) -> str:
    parts: list[str] = []
    for arg in args:
        if hasattr(arg, "deps"):
            continue
        parts.append(str(arg))
    for key, value in kwargs.items():
        if "password" in key.lower():
            parts.append(f"{key}=hidden")
        else:
            parts.append(f"{key}={value}")
    return ", ".join(parts)


def _short_result(value: Any) -> str:
    if isinstance(value, list):
        names = []
        for item in value[:8]:
            product_id = getattr(item, "product_id", "")
            names.append(product_id or str(item)[:40])
        extra = "" if len(value) <= 8 else f" (+{len(value) - 8} more)"
        return f"{len(value)} rows: {', '.join(names)}{extra}"
    dump = getattr(value, "model_dump", None)
    if dump is None:
        return str(value)
    data = dump()
    for key in list(data):
        if "password" in key.lower():
            data[key] = "hidden"
        elif isinstance(data[key], str) and len(data[key]) > 80:
            data[key] = data[key][:77] + "..."
    return json.dumps(data, default=str)


def _clip(text: str) -> str:
    text = " ".join(str(text).split())
    if len(text) <= SHORT:
        return text
    return text[: SHORT - 1] + "…"
