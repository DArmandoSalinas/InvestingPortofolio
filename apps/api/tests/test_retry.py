import pytest

from app.retry import call_with_backoff, looks_like_rate_limit, sleep_backoff


def test_rate_limit_detection():
    assert looks_like_rate_limit(RuntimeError("HTTP Error 429: Too Many Requests"))
    assert looks_like_rate_limit(text="rate limited by yahoo")
    assert not looks_like_rate_limit(RuntimeError("symbol not found"))


def test_call_with_backoff_retries_then_succeeds(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("app.retry.time.sleep", lambda seconds: sleeps.append(seconds))
    monkeypatch.setattr("app.retry.random.uniform", lambda _a, _b: 0.0)

    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("429 Too Many Requests")
        return "ok"

    assert call_with_backoff(flaky, attempts=5) == "ok"
    assert calls["n"] == 3
    assert len(sleeps) == 2


def test_call_with_backoff_gives_up_on_non_retryable():
    def boom() -> None:
        raise RuntimeError("fatal")

    with pytest.raises(RuntimeError, match="fatal"):
        call_with_backoff(boom, attempts=4)


def test_sleep_backoff_caps(monkeypatch):
    sleeps: list[float] = []
    monkeypatch.setattr("app.retry.time.sleep", lambda seconds: sleeps.append(seconds))
    monkeypatch.setattr("app.retry.random.uniform", lambda _a, _b: 0.0)
    waited = sleep_backoff(10, base=2.0, cap=8.0)
    assert waited == 8.0
    assert sleeps == [8.0]
