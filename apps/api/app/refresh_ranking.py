import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from app.market_data import download_closes, download_fundamentals
from app.render_seed import company_id
from app.scoring import price_to_sma200, score_observations, trailing_return
from app.universe import Listing, load_universe

MONTERREY = ZoneInfo("America/Monterrey")
RAW_FIELDS = (
    "revenue_growth_yoy",
    "earnings_growth_yoy",
    "pe",
    "ps",
    "ev_ebitda",
    "return_3m",
    "return_6m",
    "return_12m",
    "price_to_sma200",
)


def observe(listings: list[Listing], closes: dict[str, list[float]], fundamentals: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    for listing in listings:
        facts = fundamentals.get(listing.yahoo_symbol) or {}
        prices = closes.get(listing.yahoo_symbol) or []
        sector = listing.sector or facts.get("sector") or "unknown"
        rows.append(
            {
                "market": listing.market,
                "symbol": listing.symbol,
                "yahoo_symbol": listing.yahoo_symbol,
                "name": listing.name,
                "sector": sector,
                "currency": listing.currency,
                "universe_source": listing.universe_source,
                "revenue_growth_yoy": facts.get("revenue_growth_yoy"),
                "earnings_growth_yoy": facts.get("earnings_growth_yoy"),
                "pe": facts.get("pe"),
                "ps": facts.get("ps"),
                "ev_ebitda": facts.get("ev_ebitda"),
                "earnings_non_positive": bool(facts.get("earnings_non_positive")),
                "return_3m": trailing_return(prices, 63),
                "return_6m": trailing_return(prices, 126),
                "return_12m": trailing_return(prices, 252),
                "price_to_sma200": price_to_sma200(prices),
            }
        )
    score_observations(rows)
    return rows


def _number(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def company_payload(rows: list[dict]) -> list[dict]:
    return [
        {
            "id": str(company_id(row["market"], row["symbol"])),
            "market": row["market"],
            "symbol": row["symbol"],
            "yahoo_symbol": row["yahoo_symbol"],
            "name": row["name"],
            "sector": row["sector"],
            "currency": row["currency"],
            "universe_source": row["universe_source"],
            "active": True,
        }
        for row in rows
    ]


def snapshot_payload(rows: list[dict], as_of: str) -> list[dict]:
    payload = []
    for row in rows:
        item = {
            "company_id": str(company_id(row["market"], row["symbol"])),
            "as_of": as_of,
            "growth": row["growth"],
            "value": row["value"],
            "momentum": row["momentum"],
            "composite": row["composite"],
            "value_reference": row["value_reference"],
            "missing_fields": row["missing_fields"],
            "na_fields": row["na_fields"],
            "calculated": True,
        }
        for field in RAW_FIELDS:
            item[field] = _number(row.get(field))
        payload.append(item)
    return payload


def summarize(rows: list[dict]) -> str:
    complete = sum(1 for row in rows if row["composite"] is not None)
    highlights = sum(
        1
        for row in rows
        if row["growth"] is not None
        and row["value"] is not None
        and row["momentum"] is not None
        and row["growth"] >= 70
        and row["value"] >= 70
        and row["momentum"] >= 70
    )
    fallback = sum(1 for row in rows if row["value_reference"] == "sp500_sector")
    unknown = sum(1 for row in rows if row["sector"] == "unknown")
    return (
        f"{len(rows)} emisoras, {complete} con puntuación general, "
        f"{highlights} altas en los tres, {fallback} valores contra el S&P 500, "
        f"{unknown} sin sector"
    )


def refresh_and_store() -> str:
    listings = load_universe()
    print(f"universo {len(listings)}", flush=True)
    closes = download_closes([item.yahoo_symbol for item in listings])
    priced = sum(1 for item in listings if closes.get(item.yahoo_symbol))
    print(f"con precio {priced} de {len(listings)}", flush=True)
    fundamentals = download_fundamentals(listings)
    rows = observe(listings, closes, fundamentals)
    as_of = datetime.now(MONTERREY).date().isoformat()
    summary = summarize(rows)
    print(f"{as_of}: {summary}", flush=True)
    from app.config import get_settings
    from app.db import SupabaseRest

    db = SupabaseRest(get_settings())
    try:
        db.upsert_companies(company_payload(rows))
        db.upsert_snapshots(snapshot_payload(rows, as_of))
    finally:
        db.close()
    print("snapshot guardado", flush=True)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Calcula el ranking del día y lo guarda.")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Prueba las primeras N emisoras y no escribe en la base.",
    )
    args = parser.parse_args()
    if not args.limit:
        refresh_and_store()
        return
    listings = load_universe()[: args.limit]
    print(f"universo de prueba {len(listings)}", flush=True)
    closes = download_closes([item.yahoo_symbol for item in listings])
    fundamentals = download_fundamentals(listings)
    rows = observe(listings, closes, fundamentals)
    as_of = datetime.now(MONTERREY).date().isoformat()
    print(f"{as_of}: {summarize(rows)}", flush=True)
    print("corrida corta: no se escribió la base", flush=True)


if __name__ == "__main__":
    main()
