from pathlib import Path

from app import ranking_cache
from app.market_data import download_closes, download_fundamentals
from app.universe import Listing


def test_disk_cache_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RANKING_CACHE_DIR", str(tmp_path))
    ranking_cache.save_closes("2026-10-12", "AAPL", [1.0, 2.0, 3.0])
    ranking_cache.save_fundamentals(
        "2026-10-12",
        "AAPL",
        {"pe": 20.0, "sector": "information_technology", "revenue_growth_yoy": 0.1},
    )
    ranking_cache.mark_closes_done("2026-10-12", ["AAPL"])
    ranking_cache.mark_fundamentals_done("2026-10-12", ["AAPL"])

    assert ranking_cache.load_closes("2026-10-12", "AAPL") == [1.0, 2.0, 3.0]
    facts = ranking_cache.load_fundamentals("2026-10-12", "AAPL")
    assert facts is not None
    assert facts["pe"] == 20.0
    checkpoint = ranking_cache.load_checkpoint("2026-10-12")
    assert checkpoint["closes_done"] == ["AAPL"]
    assert checkpoint["fundamentals_done"] == ["AAPL"]


def test_download_closes_resumes_from_cache(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RANKING_CACHE_DIR", str(tmp_path))
    ranking_cache.save_closes("2026-10-12", "AAA", [10.0, 11.0])
    ranking_cache.save_closes("2026-10-12", "BBB", [20.0, 21.0])

    calls: list[list[str]] = []

    def fake_chunk(symbols: list[str]) -> dict[str, list[float]]:
        calls.append(list(symbols))
        return {symbol: [float(len(symbol))] for symbol in symbols}

    monkeypatch.setattr("app.market_data._download_chunk", fake_chunk)
    result = download_closes(["AAA", "BBB", "CCC"], as_of="2026-10-12")
    assert result["AAA"] == [10.0, 11.0]
    assert result["BBB"] == [20.0, 21.0]
    assert result["CCC"] == [3.0]
    assert calls == [["CCC"]]


def test_download_fundamentals_skips_cached(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RANKING_CACHE_DIR", str(tmp_path))
    ranking_cache.save_fundamentals(
        "2026-10-12",
        "AAA",
        {"pe": 12.0, "sector": "health_care", "revenue_growth_yoy": None, "earnings_growth_yoy": None, "ps": None, "ev_ebitda": None, "earnings_non_positive": False},
    )
    reads: list[str] = []

    def fake_read(symbol: str) -> dict:
        reads.append(symbol)
        return {
            "revenue_growth_yoy": 0.2,
            "earnings_growth_yoy": 0.1,
            "pe": 15.0,
            "ps": 3.0,
            "ev_ebitda": 10.0,
            "earnings_non_positive": False,
            "sector": "health_care",
        }

    monkeypatch.setattr("app.market_data.read_fundamentals", fake_read)
    monkeypatch.setattr("app.market_data.time.sleep", lambda _s: None)
    listings = [
        Listing(
            market="us",
            symbol="AAA",
            yahoo_symbol="AAA",
            name="Aaa",
            sector="health_care",
            currency="USD",
            universe_source="sp500",
        ),
        Listing(
            market="us",
            symbol="BBB",
            yahoo_symbol="BBB",
            name="Bbb",
            sector="health_care",
            currency="USD",
            universe_source="sp500",
        ),
    ]
    facts = download_fundamentals(listings, as_of="2026-10-12")
    assert facts["AAA"]["pe"] == 12.0
    assert facts["BBB"]["pe"] == 15.0
    assert reads == ["BBB"]
