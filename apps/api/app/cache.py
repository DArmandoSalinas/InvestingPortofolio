"""Simple in-memory cache for data sources with TTL support."""
import time
from datetime import datetime, timedelta
from typing import Any, Callable, TypeVar

from app.refresh_ranking import MONTERREY

T = TypeVar("T")

_cache: dict[str, tuple[Any, float]] = {}


def cached(key: str, ttl_seconds: int, fetch_fn: Callable[[], T]) -> T:
    """
    Cache the result of fetch_fn with the given key and TTL.
    Returns cached value if still valid, otherwise fetches new value.
    """
    now = time.time()
    if key in _cache:
        value, expires_at = _cache[key]
        if now < expires_at:
            return value
    
    value = fetch_fn()
    _cache[key] = (value, now + ttl_seconds)
    return value


def with_rate_limit_retry(func: Callable[[], T], max_retries: int = 3, delay: float = 2.0) -> T | None:
    """
    Execute func with exponential backoff for rate limit errors.
    Returns None if all retries fail due to rate limits.
    Raises non-rate-limit exceptions immediately.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as exc:
            error_text = str(exc).lower()
            # More specific detection: "rate limit", "429", or "ratelimit"
            is_rate_limit = (
                "rate limit" in error_text 
                or "ratelimit" in error_text 
                or "429" in error_text
                or "too many requests" in error_text
            )
            
            if is_rate_limit:
                last_error = exc
                if attempt < max_retries - 1:
                    wait_time = delay * (2 ** attempt)
                    timestamp = datetime.now(MONTERREY).isoformat()
                    print(
                        f"[{timestamp}] rate limit detectado, esperando {wait_time:.1f}s antes de reintentar",
                        flush=True,
                    )
                    time.sleep(wait_time)
                    continue
            else:
                # Not a rate limit error, raise immediately
                raise
    
    # All retries exhausted for rate limit errors
    return None


def clear_cache() -> None:
    """Clear all cached values."""
    _cache.clear()


def cache_stats() -> dict[str, int]:
    """Return cache statistics."""
    now = time.time()
    valid = sum(1 for _, expires_at in _cache.values() if now < expires_at)
    return {
        "total_entries": len(_cache),
        "valid_entries": valid,
        "expired_entries": len(_cache) - valid,
    }
