from app.market_data import report_from_periods
from app.signals import scoreboard


def test_the_scoreboard_ignores_open_signals_and_missing_returns():
    rows = [
        {"status": "open", "net_return": None, "spy_return": None, "btc_return": None},
        {"status": "target", "net_return": 0.04, "spy_return": 0.01, "btc_return": 0.02},
        {"status": "stop", "net_return": -0.02, "spy_return": None, "btc_return": None},
        {"status": "expired", "net_return": 0.0, "spy_return": 0.03, "btc_return": -0.01},
    ]
    board = scoreboard(rows)
    assert board["open"] == 1
    assert board["closed"] == 3
    assert board["targets"] == 1
    assert board["hit_rate"] == 1 / 3
    assert board["net_return"] == (0.04 - 0.02 + 0.0) / 3
    assert board["spy_count"] == 2
    assert board["spy_return"] == (0.01 + 0.03) / 2
    assert board["btc_count"] == 2


def test_an_empty_book_does_not_invent_a_hit_rate():
    board = scoreboard([])
    assert board["closed"] == 0
    assert board["hit_rate"] is None
    assert board["net_return"] is None


def test_the_quarterly_report_uses_the_same_quarter_a_year_earlier():
    periods = [
        ("2026-06-30", 120.0, 20.0),
        ("2026-03-31", 110.0, 18.0),
        ("2025-12-31", 100.0, 16.0),
        ("2025-09-30", 90.0, 14.0),
        ("2025-06-30", 100.0, 10.0),
    ]
    report = report_from_periods(periods)
    assert report is not None
    assert report["period"] == "2026-06-30"
    assert report["prior_period"] == "2025-06-30"
    assert report["revenue_yoy"] == (120.0 - 100.0) / 100.0
    assert report["earnings_yoy"] == (20.0 - 10.0) / 10.0


def test_one_quarter_does_not_invent_a_comparison():
    report = report_from_periods([("2026-06-30", 50.0, None)])
    assert report is not None
    assert report["prior_period"] is None
    assert report["revenue_yoy"] is None
    assert report["earnings"] is None
    assert report_from_periods([("2026-06-30", None, None)]) is None
