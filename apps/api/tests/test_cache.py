"""Tests for the cache and rate limit handling."""
import time

from app.cache import cached, cache_stats, clear_cache, with_rate_limit_retry


def test_cached_function_returns_fresh_value_on_first_call():
    call_count = {"n": 0}

    def fetch():
        call_count["n"] += 1
        return call_count["n"]

    result = cached("test_key", 10, fetch)
    assert result == 1
    assert call_count["n"] == 1


def test_cached_function_returns_cached_value_within_ttl():
    call_count = {"n": 0}

    def fetch():
        call_count["n"] += 1
        return call_count["n"]

    result1 = cached("test_key2", 10, fetch)
    result2 = cached("test_key2", 10, fetch)
    assert result1 == 1
    assert result2 == 1
    assert call_count["n"] == 1


def test_cached_function_refreshes_after_ttl_expires():
    call_count = {"n": 0}

    def fetch():
        call_count["n"] += 1
        return call_count["n"]

    result1 = cached("test_key3", 1, fetch)
    assert result1 == 1
    time.sleep(1.1)
    result2 = cached("test_key3", 1, fetch)
    assert result2 == 2
    assert call_count["n"] == 2


def test_with_rate_limit_retry_returns_value_on_success():
    def fetch():
        return "success"

    result = with_rate_limit_retry(fetch, max_retries=2, delay=0.1)
    assert result == "success"


def test_with_rate_limit_retry_retries_on_rate_limit_error():
    call_count = {"n": 0}

    def fetch():
        call_count["n"] += 1
        if call_count["n"] < 2:
            raise Exception("rate limit exceeded")
        return "success"

    result = with_rate_limit_retry(fetch, max_retries=3, delay=0.1)
    assert result == "success"
    assert call_count["n"] == 2


def test_with_rate_limit_retry_gives_up_after_max_retries():
    def fetch():
        raise Exception("rate limit 429")

    result = with_rate_limit_retry(fetch, max_retries=2, delay=0.1)
    assert result is None


def test_with_rate_limit_retry_raises_non_rate_limit_errors():
    def fetch():
        raise ValueError("this is a different error")

    try:
        with_rate_limit_retry(fetch, max_retries=2, delay=0.1)
        assert False, "should have raised ValueError"
    except ValueError as exc:
        assert "different error" in str(exc)


def test_cache_stats_reports_valid_and_expired_entries():
    clear_cache()

    def fetch():
        return "value"

    cached("key1", 10, fetch)
    cached("key2", 1, fetch)
    time.sleep(1.1)
    
    stats = cache_stats()
    assert stats["total_entries"] == 2
    assert stats["valid_entries"] == 1
    assert stats["expired_entries"] == 1
