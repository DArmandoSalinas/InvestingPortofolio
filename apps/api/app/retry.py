"""Shared retry / backoff helpers for market-data providers."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

DEFAULT_ATTEMPTS = 5
DEFAULT_BASE_SECONDS = 1.5
DEFAULT_MAX_SECONDS = 60.0


def looks_like_rate_limit(exc: BaseException | None = None, text: str = "") -> bool:
    blob = f"{exc or ''} {text}".lower()
    needles = (
        "429",
        "too many requests",
        "rate limit",
        "rate limited",
        "try again later",
        "temporarily unavailable",
        "unexpected eof",
        "timed out",
        "timeout",
        "connection reset",
    )
    return any(needle in blob for needle in needles)


def sleep_backoff(attempt: int, *, base: float = DEFAULT_BASE_SECONDS, cap: float = DEFAULT_MAX_SECONDS) -> float:
    delay = min(cap, base * (2**attempt))
    jitter = random.uniform(0, delay * 0.25)
    total = delay + jitter
    time.sleep(total)
    return total


def call_with_backoff(
    fn: Callable[[], T],
    *,
    attempts: int = DEFAULT_ATTEMPTS,
    should_retry: Callable[[BaseException], bool] | None = None,
    on_retry: Callable[[int, BaseException, float], None] | None = None,
) -> T:
    last: BaseException | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — provider surface is broad
            last = exc
            retry = looks_like_rate_limit(exc) if should_retry is None else should_retry(exc)
            if attempt >= attempts - 1 or not retry:
                raise
            waited = sleep_backoff(attempt)
            if on_retry is not None:
                on_retry(attempt + 1, exc, waited)
    assert last is not None
    raise last
