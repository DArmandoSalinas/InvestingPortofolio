from datetime import datetime
from zoneinfo import ZoneInfo

from app.brief import brief_message, open_signals, ranking_brief, session_date
from app.mailer import mail_problem

NEW_YORK = ZoneInfo("America/New_York")


def company(symbol: str, composite: int | None, growth: int, value: int, momentum: int) -> dict:
    return {
        "market": "us",
        "symbol": symbol,
        "name": symbol,
        "growth": growth,
        "value": value,
        "momentum": momentum,
        "composite": composite,
    }


def test_the_brief_starts_thirty_minutes_before_the_new_york_open():
    assert session_date(datetime(2026, 7, 15, 8, 59, tzinfo=NEW_YORK)) is None
    assert session_date(datetime(2026, 7, 15, 9, 0, tzinfo=NEW_YORK)).isoformat() == "2026-07-15"
    assert session_date(datetime(2026, 1, 15, 8, 59, tzinfo=NEW_YORK)) is None
    assert session_date(datetime(2026, 1, 17, 10, 0, tzinfo=NEW_YORK)).isoformat() == "2026-01-17"


def test_the_first_calculated_day_lists_highlights_without_inventing_changes():
    current = [
        company("AAA", 80, 80, 80, 80),
        company("BBB", 50, 40, 90, 20),
        company("CCC", None, 90, None, 90),
    ]
    report = ranking_brief(current, None, 70)
    assert report["compared"] is False
    assert [item["symbol"] for item in report["highlights"]] == ["AAA"]
    assert report["entered"] == []
    assert report["left"] == []
    assert report["movers"] == []


def test_changes_use_only_scores_present_on_both_days():
    previous = [
        company("AAA", 70, 70, 70, 70),
        company("BBB", 90, 90, 90, 90),
        company("DDD", None, 80, None, 80),
    ]
    current = [
        company("AAA", 88, 90, 80, 94),
        company("BBB", 60, 50, 60, 70),
        company("CCC", 75, 80, 70, 75),
        company("DDD", 80, 80, 80, 80),
    ]
    report = ranking_brief(current, previous, 70)
    assert [item["symbol"] for item in report["entered"]] == ["DDD", "CCC"]
    assert [item["symbol"] for item in report["left"]] == ["BBB"]
    assert report["movers"][0]["symbol"] == "BBB"
    assert report["movers"][0]["delta"] == -30
    assert all(item["symbol"] != "DDD" for item in report["movers"])


def test_only_open_signals_go_into_the_brief():
    rows = [
        {"status": "open", "symbol": "NVDA", "name": "NVIDIA", "setup": "impulso", "as_of": "2026-10-05", "confidence": 95, "asset_class": "stock"},
        {"status": "stop", "symbol": "AAPL", "name": "Apple", "setup": "retroceso", "as_of": "2026-10-01", "confidence": 80, "asset_class": "stock"},
    ]
    assert [item["symbol"] for item in open_signals(rows)] == ["NVDA"]


def test_the_daily_letter_uses_only_the_stored_names():
    text = brief_message(
        "Resumen del día",
        {
            "highlights": [{"symbol": "SMCI"}],
            "entered": [],
            "left": [],
            "movers": [{"symbol": "MU", "before": 80, "after": 89}],
            "signals": [{"symbol": "NVDA"}],
        },
        "http://localhost:3000",
    )
    assert "SMCI" in text
    assert "MU: 80 a 89" in text
    assert "NVDA" in text
    assert text.endswith("http://localhost:3000/resumen")


def test_a_rate_limit_becomes_a_spanish_mail_error():
    assert "demasiados" in mail_problem("over_email_send_rate_limit")
    assert mail_problem("email_not_allowed") == "Ese correo no está autorizado"
