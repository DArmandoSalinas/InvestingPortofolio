from datetime import date

from app.explain import growth_note, momentum_note, value_note
from app.schedule import ranking_due


def test_ranking_refreshes_only_when_today_is_missing():
    today = date(2026, 10, 5)
    assert ranking_due(None, False, today)
    assert ranking_due(date(2026, 10, 4), True, today)
    assert ranking_due(today, False, today)
    assert not ranking_due(today, True, today)


def test_notes_use_only_stored_inputs():
    row = {
        "revenue_growth_yoy": 0.30,
        "earnings_growth_yoy": None,
        "missing_fields": ["earnings_growth_yoy", "return_12m", "ps"],
        "na_fields": ["ev_ebitda"],
        "pe": 12.5,
        "ps": None,
        "ev_ebitda": None,
        "value": 80,
        "value_reference": "sp500_sector",
        "return_3m": -0.10,
        "return_6m": 0.05,
        "return_12m": None,
        "price_to_sma200": 1.08,
    }
    assert growth_note(row) == (
        "Ingresos 30,0% y falta utilidades contra el año anterior. La escala va de −20% a +30%."
    )
    assert "P/E 12,5" in value_note(row)
    assert "Falta P/S" in value_note(row)
    assert "EV/EBITDA no aplica" in value_note(row)
    assert "S&P 500" in value_note(row)
    momentum = momentum_note(row)
    assert "63 sesiones -10,0%" in momentum
    assert "126 sesiones 5,0%" in momentum
    assert "Faltan 252 sesiones" in momentum
    assert "1,08" in momentum
