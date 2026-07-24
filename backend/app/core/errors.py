"""Shared error handling: user-friendly messages + a tool wrapper.

Tools must never raise — the agent recovers gracefully from an
`{"error": ...}` payload but crashes on an unhandled exception. `@tool_errors`
enforces that contract in one place, replacing the try/except blocks that were
duplicated across every tool.
"""

import asyncio
import functools

from app.core.logging import get_logger

logger = get_logger(__name__)


def friendly_error(exc: Exception) -> str:
    """Map an exception to a short, user-facing message (no internals leaked)."""
    text = str(exc).lower()
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)) or "timeout" in text:
        return "The request took too long. Please try again."
    if "429" in text or "rate limit" in text:
        return "The service is busy right now. Please wait a moment and try again."
    if "connection" in text or "network" in text:
        return "Unable to reach AI services. Please try again."
    return "Something went wrong processing your request. Please try again."


def tool_errors(fn):
    """Wrap a tool so any exception becomes `{"error": <friendly message>}`."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — tools must never propagate
            logger.exception("Tool %s failed", fn.__name__)
            return {"error": friendly_error(exc)}

    return wrapper
