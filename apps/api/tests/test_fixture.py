from app.fixture_data import COMPANIES, RAW_FIELDS
from app.render_seed import SEED_PATH, render_seed
from app.scoring import composite_of, is_highlight
from app.sectors import SECTORS


def test_fixture_has_twenty_five_real_names() -> None:
    assert len(COMPANIES) == 25
    assert len({(row["market"], row["symbol"]) for row in COMPANIES}) == 25


def test_scores_follow_the_composite_rule() -> None:
    for row in COMPANIES:
        assert row["composite"] == composite_of(row["growth"], row["value"], row["momentum"])
        for field in ("growth", "value", "momentum", "composite"):
            if row[field] is not None:
                assert 0 <= row[field] <= 100
        assert row["sector"] in SECTORS


def test_gaps_are_not_stored_as_zero() -> None:
    for row in COMPANIES:
        overlap = set(row["missing_fields"]) & set(row["na_fields"])
        assert overlap == set()
        for field in row["missing_fields"] + row["na_fields"]:
            assert field in RAW_FIELDS
            assert row[field] is None


def test_value_reference_matches_the_market_rule() -> None:
    for row in COMPANIES:
        if row["value"] is None:
            assert row["value_reference"] is None
        elif row["market"] == "mx":
            assert row["value_reference"] == "sp500_sector"
        else:
            assert row["value_reference"] == "local"


def test_required_cases_exist() -> None:
    highlights = [row["symbol"] for row in COMPANIES if is_highlight(row, 70)]
    assert set(highlights) == {"MSFT", "AAPL", "GOOGL", "WALMEX", "GMEXICOB"}
    assert any(
        row["composite"] is not None and row["composite"] < 70
        and all(row[field] is not None for field in ("growth", "value", "momentum"))
        for row in COMPANIES
    )
    assert any(row["composite"] is None for row in COMPANIES)
    assert any(
        row["sector"] == "financials" and "ev_ebitda" in row["na_fields"] for row in COMPANIES
    )
    assert any(row["market"] == "mx" and row["value_reference"] == "sp500_sector" for row in COMPANIES)
    assert any(row["missing_fields"] for row in COMPANIES)
    assert any("pe" in row["na_fields"] and row["value"] is not None for row in COMPANIES)


def test_seed_sql_matches_the_fixture() -> None:
    rendered = render_seed()
    assert SEED_PATH.read_text() == rendered
    for row in COMPANIES:
        assert row["symbol"] in rendered
