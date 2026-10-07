from datetime import date, timedelta

from app.investor import fit_note, normalize_holding, parse_allocation, position_view, rollup, spanned_return


def bars(days: int, start: float = 100) -> list[dict]:
    first = date(2025, 1, 1)
    return [
        {"time": (first + timedelta(days=index)).isoformat(), "close": start + index}
        for index in range(days)
    ]


def test_a_year_of_prices_reports_the_real_dates_and_a_short_series_does_not():
    series = bars(400, 100)
    report = spanned_return(series)
    assert report is not None
    start = date.fromisoformat(report["start"])
    end = date.fromisoformat(report["end"])
    assert end.isoformat() == series[-1]["time"]
    assert (end - start).days >= 340
    chosen = next(bar for bar in series if bar["time"] == report["start"])
    assert report["value"] == (series[-1]["close"] / chosen["close"]) - 1
    assert spanned_return(bars(30)) is None


def test_allocation_weights_have_to_sum_to_one_hundred():
    sleeves = [
        {"id": sleeve_id, "weight": 20, "reason": sleeve_id}
        for sleeve_id in ("cetes", "ahorro", "etf", "acciones", "crypto")
    ]
    parsed = parse_allocation({"summary": "Mezcla", "risk": "Puede bajar", "sleeves": sleeves})
    assert parsed is not None
    assert sum(item["weight"] for item in parsed["sleeves"]) == 100
    sleeves[0]["weight"] = 19
    assert parse_allocation({"sleeves": sleeves}) is None


def test_a_missing_price_is_not_stored_as_zero_and_blocks_the_total():
    carried = position_view(
        {"id": "1", "asset_class": "cetes", "symbol": "CETES", "name": "CETES", "quantity": 1000, "unit_cost": 1, "currency": "MXN", "opened_on": "2026-01-01", "yahoo_symbol": None},
        None,
        None,
    )
    missing = position_view(
        {"id": "2", "asset_class": "stock", "symbol": "AAPL", "name": "AAPL", "quantity": 2, "unit_cost": 100, "currency": "USD", "opened_on": "2026-01-01", "yahoo_symbol": "AAPL"},
        None,
        None,
    )
    priced = position_view(
        {"id": "3", "asset_class": "stock", "symbol": "MSFT", "name": "MSFT", "quantity": 1, "unit_cost": 100, "currency": "USD", "opened_on": "2026-01-01", "yahoo_symbol": "MSFT"},
        110,
        "2026-10-05",
    )
    assert carried["price_state"] == "carried"
    assert carried["pnl"] is None
    assert missing["market_value"] is None
    assert priced["pnl"] == (110 / 100) - 1
    totals = {row["currency"]: row for row in rollup([carried, missing, priced])}
    assert totals["MXN"]["market_value"] == 1000
    assert totals["USD"]["market_value"] is None
    assert totals["USD"]["cost"] == 300


def test_mexico_listing_uses_pesos_and_a_future_date_is_rejected():
    holding = normalize_holding("stock", "walmex", "mx", 10, 50, None, date(2026, 10, 1), date(2026, 10, 5))
    assert holding["yahoo_symbol"] == "WALMEX.MX"
    assert holding["currency"] == "MXN"
    try:
        normalize_holding("stock", "AAPL", "us", 1, 10, None, date(2026, 10, 6), date(2026, 10, 5))
    except ValueError as exc:
        assert "posterior" in str(exc)
    else:
        raise AssertionError("expected a future date to fail")


def test_fit_describes_the_declared_horizon_without_a_trade():
    note = fit_note("crypto", "bajo", 1)
    assert "compra" not in note.lower()
    assert "venta" not in note.lower()
