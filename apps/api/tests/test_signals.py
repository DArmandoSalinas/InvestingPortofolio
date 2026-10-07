from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.signals import buy_hold, completed_bars, evaluate, propose


def bars(closes: list[float]) -> list[dict]:
    start = date(2026, 1, 1)
    return [
        {
            "time": (start + timedelta(days=index)).isoformat(),
            "open": close,
            "high": close,
            "low": close,
            "close": close,
        }
        for index, close in enumerate(closes)
    ]


def test_an_uptrend_proposes_an_impulse_and_a_flat_market_proposes_nothing():
    signal = propose(bars([100 + index for index in range(60)]), "stock")
    assert signal is not None
    assert signal["setup"] == "impulso"
    assert signal["confidence"] == 75
    assert signal["stop"] < signal["entry"] < signal["target"]
    assert signal["commission_rate"] == 0.001
    assert propose(bars([100.0] * 60), "crypto") is None


def test_same_day_stop_wins_over_the_target():
    outcome = evaluate(
        entry=100,
        stop=95,
        target=110,
        future=[{"time": "2026-04-01", "high": 112, "low": 94, "close": 108}],
        horizon=10,
        commission=0.001,
    )
    assert outcome is not None
    assert outcome["status"] == "stop"
    assert outcome["exit_price"] == 95
    assert outcome["net_return"] == (95 / 100 - 1) - 0.001


def test_the_horizon_closes_at_the_last_close_when_neither_level_is_hit():
    future = [
        {"time": f"2026-05-{day:02d}", "high": 101, "low": 99, "close": 100 + day / 100}
        for day in range(1, 11)
    ]
    outcome = evaluate(100, 90, 120, future, 10, 0.002)
    assert outcome is not None
    assert outcome["status"] == "expired"
    assert outcome["exit_price"] == future[-1]["close"]
    assert evaluate(100, 90, 120, future[:3], 10, 0.002) is None


def test_an_unfinished_session_is_not_used():
    series = bars([100 + index for index in range(60)])
    last = series[-1]["time"]
    morning = datetime(2026, 3, 1, 10, 0, tzinfo=ZoneInfo("America/New_York"))
    assert completed_bars(series, "stock", morning)[-1]["time"] != last
    closed = datetime(2026, 3, 1, 16, 0, tzinfo=ZoneInfo("America/New_York"))
    assert completed_bars(series, "stock", closed)[-1]["time"] == last
    late_utc = datetime(2026, 3, 1, 23, 0, tzinfo=timezone.utc)
    assert completed_bars(series, "crypto", late_utc)[-1]["time"] != last
    next_utc_day = datetime(2026, 3, 2, 0, 0, tzinfo=timezone.utc)
    assert completed_bars(series, "crypto", next_utc_day)[-1]["time"] == last


def test_buy_and_hold_stays_empty_without_both_dates():
    series = bars([100, 110])
    assert buy_hold(series, series[0]["time"], series[1]["time"]) == (110 / 100) - 1
    assert buy_hold(series, series[0]["time"], "2026-12-31") is None
