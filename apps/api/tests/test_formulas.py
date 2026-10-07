from app.scoring import (
    growth_score,
    map_scale,
    momentum_score,
    price_to_sma200,
    score_observations,
    trailing_return,
)


def test_scales_hit_the_anchors_and_clamp():
    assert map_scale(-0.20, -0.20, 0.0, 0.30) == 0
    assert map_scale(0.0, -0.20, 0.0, 0.30) == 50
    assert map_scale(0.30, -0.20, 0.0, 0.30) == 100
    assert map_scale(0.15, -0.20, 0.0, 0.30) == 75
    assert map_scale(-1, -0.30, 0.0, 0.40) == 0
    assert map_scale(1, -0.30, 0.0, 0.40) == 100
    assert map_scale(0.70, 0.70, 1.00, 1.30) == 0
    assert map_scale(1.00, 0.70, 1.00, 1.30) == 50
    assert map_scale(1.30, 0.70, 1.00, 1.30) == 100
    assert map_scale(0.85, 0.70, 1.00, 1.30) == 25


def test_growth_averages_what_exists_and_stays_null_without_inputs():
    score, missing = growth_score(0.30, None)
    assert score == 100
    assert missing == ["earnings_growth_yoy"]
    score, missing = growth_score(None, None)
    assert score is None
    assert missing == ["revenue_growth_yoy", "earnings_growth_yoy"]


def test_momentum_uses_sessions_and_the_200_day_mean():
    closes = [10.0] * 252 + [12.0]
    assert trailing_return(closes, 63) == (12 / 10) - 1
    assert trailing_return([10.0] * 63, 63) is None
    assert price_to_sma200([10.0] * 199) is None
    assert price_to_sma200([10.0] * 200) == 1
    score, missing = momentum_score(0.40, None, -0.30, 1.0)
    assert missing == ["return_6m"]
    assert score == (100 + 0 + 50 + 1) // 3


def test_local_value_is_an_inverted_percentile_and_cheaper_scores_higher():
    rows = []
    for index, pe in enumerate((10, 12, 14, 16, 18, 20, 22, 24)):
        rows.append(
            {
                "market": "us",
                "sector": "energy",
                "symbol": f"E{index}",
                "pe": pe,
                "ps": None,
                "ev_ebitda": None,
                "earnings_non_positive": False,
                "revenue_growth_yoy": 0.0,
                "earnings_growth_yoy": 0.0,
                "return_3m": 0.0,
                "return_6m": 0.0,
                "return_12m": 0.0,
                "price_to_sma200": 1.0,
            }
        )
    score_observations(rows)
    by_pe = {row["pe"]: row for row in rows}
    assert by_pe[10]["value"] == 100
    assert by_pe[24]["value"] == 0
    assert by_pe[16]["value"] == 57
    assert by_pe[10]["value_reference"] == "local"
    assert "ps" in by_pe[10]["missing_fields"]
    assert by_pe[10]["composite"] == (50 + 100 + 50 + 1) // 3


def test_mexico_uses_the_sp500_sector_when_the_local_group_is_small():
    rows = [
        {
            "market": "us",
            "sector": "materials",
            "pe": pe,
            "ps": None,
            "ev_ebitda": None,
            "earnings_non_positive": False,
            "revenue_growth_yoy": 0.0,
            "earnings_growth_yoy": 0.0,
            "return_3m": 0.0,
            "return_6m": 0.0,
            "return_12m": 0.0,
            "price_to_sma200": 1.0,
        }
        for pe in (10, 20, 30, 40, 50, 60, 70, 80)
    ]
    rows.append(
        {
            "market": "mx",
            "sector": "materials",
            "pe": 10,
            "ps": None,
            "ev_ebitda": None,
            "earnings_non_positive": False,
            "revenue_growth_yoy": 0.0,
            "earnings_growth_yoy": 0.0,
            "return_3m": 0.0,
            "return_6m": 0.0,
            "return_12m": 0.0,
            "price_to_sma200": 1.0,
        }
    )
    score_observations(rows)
    mexico = rows[-1]
    assert mexico["value"] == 88
    assert mexico["value_reference"] == "sp500_sector"
    assert rows[0]["value_reference"] == "local"
    assert rows[0]["value"] == 100


def test_value_stays_null_when_neither_group_has_eight_names():
    rows = [
        {
            "market": "us",
            "sector": "utilities",
            "pe": 10 + index,
            "ps": None,
            "ev_ebitda": None,
            "earnings_non_positive": False,
            "revenue_growth_yoy": 0.0,
            "earnings_growth_yoy": 0.0,
            "return_3m": 0.0,
            "return_6m": 0.0,
            "return_12m": 0.0,
            "price_to_sma200": 1.0,
        }
        for index in range(7)
    ]
    score_observations(rows)
    assert all(row["value"] is None for row in rows)
    assert all(row["value_reference"] is None for row in rows)
    assert all(row["composite"] is None for row in rows)
    assert "pe" not in rows[0]["missing_fields"]


def test_financials_ignore_ev_ebitda_and_negative_earnings_make_pe_not_applicable():
    rows = []
    for index in range(8):
        rows.append(
            {
                "market": "us",
                "sector": "financials",
                "pe": 10 + index * 10,
                "ps": None,
                "ev_ebitda": 5,
                "earnings_non_positive": False,
                "revenue_growth_yoy": 0.0,
                "earnings_growth_yoy": 0.0,
                "return_3m": 0.0,
                "return_6m": 0.0,
                "return_12m": 0.0,
                "price_to_sma200": 1.0,
            }
        )
    rows[0]["ev_ebitda"] = 99
    rows.append(
        {
            "market": "us",
            "sector": "energy",
            "pe": 4,
            "ps": 8,
            "ev_ebitda": 6,
            "earnings_non_positive": True,
            "revenue_growth_yoy": None,
            "earnings_growth_yoy": None,
            "return_3m": None,
            "return_6m": None,
            "return_12m": None,
            "price_to_sma200": None,
        }
    )
    for index in range(7):
        rows.append(
            {
                "market": "us",
                "sector": "energy",
                "pe": 20 + index,
                "ps": 2 + index,
                "ev_ebitda": 4,
                "earnings_non_positive": False,
                "revenue_growth_yoy": 0.0,
                "earnings_growth_yoy": 0.0,
                "return_3m": 0.0,
                "return_6m": 0.0,
                "return_12m": 0.0,
                "price_to_sma200": 1.0,
            }
        )
    score_observations(rows)
    cheapest_bank = rows[0]
    assert cheapest_bank["value"] == 100
    assert cheapest_bank["ev_ebitda"] is None
    assert "ev_ebitda" in cheapest_bank["na_fields"]
    assert "ev_ebitda" not in cheapest_bank["missing_fields"]
    loss = next(row for row in rows if row["sector"] == "energy" and row["revenue_growth_yoy"] is None)
    assert loss["pe"] is None
    assert "pe" in loss["na_fields"]
    assert "pe" not in loss["missing_fields"]
    assert loss["value"] is not None
    assert loss["growth"] is None
    assert loss["composite"] is None
    assert set(loss["missing_fields"]).isdisjoint(loss["na_fields"])
