import html
import re
from dataclasses import dataclass
from io import StringIO

import httpx

SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
IPC_URL = "https://en.wikipedia.org/wiki/%C3%8Dndice_de_Precios_y_Cotizaciones"
WIKI_HEADERS = {
    "User-Agent": "InvestingPortfolio/0.2 (ranking local; admin@estudio.local)"
}

# Rebalanceos publicados en 2026. Si la tabla ya los trae, no se duplican.
IPC_DROPPED = {"CUERVO", "TLEVISACPO"}
ALPEK_SYMBOL = "ALPEKA"

GICS_BY_NAME = {
    "energy": "energy",
    "materials": "materials",
    "basic materials": "materials",
    "industrials": "industrials",
    "consumer discretionary": "consumer_discretionary",
    "consumer cyclical": "consumer_discretionary",
    "consumer staples": "consumer_staples",
    "consumer defensive": "consumer_staples",
    "health care": "health_care",
    "healthcare": "health_care",
    "financials": "financials",
    "financial": "financials",
    "financial services": "financials",
    "information technology": "information_technology",
    "technology": "information_technology",
    "communication services": "communication_services",
    "telecommunication services": "communication_services",
    "utilities": "utilities",
    "real estate": "real_estate",
}


@dataclass(frozen=True)
class Listing:
    market: str
    symbol: str
    yahoo_symbol: str
    name: str
    sector: str | None
    currency: str
    universe_source: str


def gics_code(name: str | None) -> str | None:
    if not name:
        return None
    return GICS_BY_NAME.get(" ".join(name.strip().lower().split()))


def compact_bmv(ticker: str) -> str:
    return "".join(ticker.upper().split())


def cell_text(cell: str) -> str:
    text = re.sub(r"<[^>]+>", "", cell)
    return " ".join(html.unescape(text).replace("\xa0", " ").split())


def listing_from_bmv(name: str, ticker: str, sector_name: str) -> Listing:
    symbol = compact_bmv(ticker)
    return Listing(
        market="mx",
        symbol=symbol,
        yahoo_symbol=f"{symbol}.MX",
        name=name,
        sector=gics_code(sector_name),
        currency="MXN",
        universe_source="ipc",
    )


def parse_ipc_html(page: str) -> list[Listing]:
    start = page.find('id="Components"')
    chunk = page[start:] if start >= 0 else page
    end = chunk.find('id="Annual_Returns"')
    if end >= 0:
        chunk = chunk[:end]
    listings: list[Listing] = []
    seen: set[str] = set()
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", chunk, flags=re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, flags=re.S)
        if len(cells) < 2:
            continue
        name = cell_text(cells[0])
        ticker = cell_text(cells[1])
        sector_name = cell_text(cells[2]) if len(cells) > 2 else ""
        if not ticker or ticker.lower() in {"ticker", "symbol"}:
            continue
        listing = listing_from_bmv(name, ticker, sector_name)
        if not listing.symbol or listing.symbol in seen:
            continue
        seen.add(listing.symbol)
        listings.append(listing)
    return listings


def apply_ipc_adjustments(listings: list[Listing]) -> list[Listing]:
    kept = [item for item in listings if item.symbol not in IPC_DROPPED]
    if any(item.symbol == ALPEK_SYMBOL for item in kept):
        return kept
    kept.append(
        Listing(
            market="mx",
            symbol=ALPEK_SYMBOL,
            yahoo_symbol=f"{ALPEK_SYMBOL}.MX",
            name="Alpek",
            sector="materials",
            currency="MXN",
            universe_source="ipc",
        )
    )
    return kept


def parse_sp500_html(page: str) -> list[Listing]:
    import pandas as pd

    tables = pd.read_html(StringIO(page))
    frame = None
    for table in tables:
        columns = {str(column).strip() for column in table.columns}
        if {"Symbol", "Security", "GICS Sector"} <= columns:
            frame = table
            break
    if frame is None:
        raise ValueError("Wikipedia no trajo la tabla del S&P 500")
    listings: list[Listing] = []
    seen: set[str] = set()
    for record in frame.to_dict(orient="records"):
        symbol = re.sub(r"\[.*?\]", "", str(record["Symbol"])).strip().upper()
        if not symbol or symbol == "NAN":
            continue
        if symbol in seen:
            continue
        seen.add(symbol)
        name = str(record["Security"]).strip()
        listings.append(
            Listing(
                market="us",
                symbol=symbol,
                yahoo_symbol=symbol.replace(".", "-"),
                name=name,
                sector=gics_code(str(record["GICS Sector"])),
                currency="USD",
                universe_source="sp500",
            )
        )
    return listings


def _wiki(url: str) -> str:
    response = httpx.get(url, headers=WIKI_HEADERS, timeout=30, follow_redirects=True)
    response.raise_for_status()
    return response.text


def load_universe() -> list[Listing]:
    sp500 = parse_sp500_html(_wiki(SP500_URL))
    ipc = apply_ipc_adjustments(parse_ipc_html(_wiki(IPC_URL)))
    if len(sp500) < 400:
        raise RuntimeError(f"El S&P 500 llegó incompleto ({len(sp500)})")
    if len(ipc) < 25:
        raise RuntimeError(f"El IPC llegó incompleto ({len(ipc)})")
    return [*sp500, *ipc]
