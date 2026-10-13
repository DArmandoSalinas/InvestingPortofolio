import math
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app import ranking_cache
from app.retry import call_with_backoff, looks_like_rate_limit
from app.universe import Listing, gics_code

PRICE_CHUNK = 40
FUNDAMENTAL_WORKERS = 4
CHUNK_PAUSE_SECONDS = 1.0
FUNDAMENTAL_PAUSE_SECONDS = 0.35

# Símbolos que ya no cotizan en Yahoo pero pueden aparecer en Wikipedia
DELISTED_SYMBOLS = {
    "ELEKTRA.MX",  # Ya no cotiza
    "ALFAA.MX",    # Ya no cotiza
}


def _is_delisted(symbol: str) -> bool:
    """Verifica si un símbolo está en la lista de dados de baja."""
    return symbol in DELISTED_SYMBOLS


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _price_series(frame: Any, symbol: str, field: str) -> Any:
    import pandas as pd

    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return None
    series = None
    if isinstance(frame.columns, pd.MultiIndex):
        level0 = {str(value) for value in frame.columns.get_level_values(0)}
        level1 = {str(value) for value in frame.columns.get_level_values(1)}
        if symbol in level0:
            block = frame[symbol]
            if field in block.columns:
                series = block[field]
        elif symbol in level1:
            block = frame.xs(symbol, axis=1, level=1)
            if field in block.columns:
                series = block[field]
    elif field in frame.columns:
        series = frame[field]
    if isinstance(series, pd.DataFrame):
        series = series.iloc[:, 0]
    return series


def closes_from_frame(frame: Any, symbol: str, alone: bool = False) -> list[float]:
    del alone
    if frame is None:
        return []
    series = _price_series(frame, symbol, "Close")
    if series is None:
        return []
    values: list[float] = []
    for raw in series.dropna().tolist():
        number = _finite(raw)
        if number is not None:
            values.append(number)
    return values


def _download_chunk(symbols: list[str]) -> dict[str, list[float]]:
    import yfinance as yf
    from app.cache import with_rate_limit_retry

    def fetch():
        return yf.download(
            symbols,
            period="2y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
            group_by="ticker",
        )
    
    frame = with_rate_limit_retry(fetch, max_retries=3, delay=2.0)
    if frame is None:
        return {symbol: [] for symbol in symbols}
    
    found = {symbol: closes_from_frame(frame, symbol) for symbol in symbols}
    missing = [symbol for symbol, closes in found.items() if not closes]
    for symbol in missing:
        def fetch_single():
            return yf.download(
                [symbol],
                period="2y",
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=False,
            )
        
        try:
            single = with_rate_limit_retry(fetch_single, max_retries=2, delay=1.0)
            if single is not None:
                found[symbol] = closes_from_frame(single, symbol)
        except Exception:
            continue
    return found


def download_closes(symbols: list[str], *, as_of: str | None = None) -> dict[str, list[float]]:
    closes: dict[str, list[float]] = {}
    unique = list(dict.fromkeys(symbols))

    # Filtrar símbolos dados de baja
    active = [s for s in unique if not _is_delisted(s)]
    delisted = [s for s in unique if _is_delisted(s)]

    if delisted:
        print(f"omitiendo {len(delisted)} símbolos dados de baja: {', '.join(delisted)}", flush=True)
        for symbol in delisted:
            closes[symbol] = []

    pending: list[str] = []
    if as_of:
        for symbol in active:
            cached = ranking_cache.load_closes(as_of, symbol)
            if cached:
                closes[symbol] = cached
            else:
                pending.append(symbol)
        if closes:
            print(f"precios en caché {len(closes) - len(delisted)} de {len(active)}", flush=True)
    else:
        pending = active

    for start in range(0, len(pending), PRICE_CHUNK):
        chunk = pending[start : start + PRICE_CHUNK]
        print(
            f"precios {start + 1}-{start + len(chunk)} de {len(pending)} pendientes",
            flush=True,
        )
        batch = _download_chunk(chunk)
        closes.update(batch)
        if as_of:
            for symbol, values in batch.items():
                if values:
                    ranking_cache.save_closes(as_of, symbol, values)
            ranking_cache.mark_closes_done(as_of, list(batch))
        if start + PRICE_CHUNK < len(pending):
            time.sleep(CHUNK_PAUSE_SECONDS)
    return closes


def _yoy(frame: Any, row_name: str) -> float | None:
    if frame is None or getattr(frame, "empty", True) or row_name not in frame.index:
        return None
    series = frame.loc[row_name].dropna().sort_index(ascending=False)
    if len(series) < 2:
        return None
    latest = _finite(series.iloc[0])
    previous = _finite(series.iloc[1])
    if latest is None or previous is None or previous == 0:
        return None
    return (latest - previous) / abs(previous)


def _annual_growth(ticker: Any) -> tuple[float | None, float | None]:
    try:
        income = ticker.income_stmt
    except Exception:
        return None, None
    return _yoy(income, "Total Revenue"), _yoy(income, "Net Income")


def report_from_periods(
    periods: list[tuple[str, float | None, float | None]],
) -> dict[str, Any] | None:
    rows = [
        (period[:10], revenue, earnings)
        for period, revenue, earnings in periods
        if revenue is not None or earnings is not None
    ]
    if not rows:
        return None
    period, revenue, earnings = rows[0]
    prior = rows[4] if len(rows) >= 5 else None
    revenue_yoy = None
    earnings_yoy = None
    prior_period = None
    if prior is not None:
        prior_period, prior_revenue, prior_earnings = prior
        if revenue is not None and prior_revenue not in (None, 0):
            revenue_yoy = (revenue - prior_revenue) / abs(prior_revenue)
        if earnings is not None and prior_earnings not in (None, 0):
            earnings_yoy = (earnings - prior_earnings) / abs(prior_earnings)
    return {
        "period": period,
        "revenue": revenue,
        "earnings": earnings,
        "prior_period": prior_period,
        "revenue_yoy": revenue_yoy,
        "earnings_yoy": earnings_yoy,
    }


def _statement_cell(frame: Any, row_name: str, column: Any) -> float | None:
    if frame is None or getattr(frame, "empty", True) or row_name not in frame.index:
        return None
    try:
        return _finite(frame.at[row_name, column])
    except (KeyError, TypeError, ValueError):
        return None


_REPORT_CACHE: dict[str, tuple[float, dict[str, Any] | None]] = {}


def quarterly_report(yahoo_symbol: str) -> dict[str, Any] | None:
    import time

    import yfinance as yf

    cached = _REPORT_CACHE.get(yahoo_symbol)
    now = time.time()
    if cached and now - cached[0] < _BAR_TTL_SECONDS:
        return cached[1]
    report = None
    try:
        frame = yf.Ticker(yahoo_symbol).quarterly_income_stmt
        if frame is not None and not getattr(frame, "empty", True):
            columns = sorted(frame.columns, reverse=True)
            periods: list[tuple[str, float | None, float | None]] = []
            for column in columns:
                day = column.date().isoformat() if hasattr(column, "date") else str(column)[:10]
                periods.append(
                    (
                        day,
                        _statement_cell(frame, "Total Revenue", column),
                        _statement_cell(frame, "Net Income", column),
                    )
                )
            report = report_from_periods(periods)
    except Exception:
        report = None
    _REPORT_CACHE[yahoo_symbol] = (now, report)
    return report


_EARNINGS_CACHE: dict[str, tuple[float, str | None]] = {}


def next_earnings_date(yahoo_symbol: str) -> str | None:
    """
    Obtiene la próxima fecha de reporte de resultados.

    Args:
        yahoo_symbol: Símbolo de Yahoo Finance

    Returns:
        Fecha en formato YYYY-MM-DD o None si no está disponible
    """
    import time

    import yfinance as yf

    cached = _EARNINGS_CACHE.get(yahoo_symbol)
    now = time.time()
    if cached and now - cached[0] < _BAR_TTL_SECONDS:
        return cached[1]

    earnings_date = None
    try:
        ticker = yf.Ticker(yahoo_symbol)
        # Intentar obtener del calendario
        calendar = ticker.calendar
        if calendar is not None and "Earnings Date" in calendar:
            dates = calendar["Earnings Date"]
            if hasattr(dates, "iloc") and len(dates) > 0:
                # Tomar la primera fecha disponible
                first_date = dates.iloc[0]
                if hasattr(first_date, "date"):
                    earnings_date = first_date.date().isoformat()
                elif isinstance(first_date, str):
                    earnings_date = first_date[:10]
    except Exception:
        pass

    _EARNINGS_CACHE[yahoo_symbol] = (now, earnings_date)
    return earnings_date


def empty_fundamentals() -> dict[str, Any]:
    return {
        "revenue_growth_yoy": None,
        "earnings_growth_yoy": None,
        "pe": None,
        "ps": None,
        "ev_ebitda": None,
        "earnings_non_positive": False,
        "sector": None,
        "operating_margin": None,
        "net_margin": None,
        "roe": None,
        "debt_to_equity": None,
        "fcf_yield": None,
    }


def read_fundamentals(yahoo_symbol: str) -> dict[str, Any]:
    import yfinance as yf
    from app.cache import with_rate_limit_retry

    empty = empty_fundamentals()
    
    def fetch():
        ticker = yf.Ticker(yahoo_symbol)
        info = ticker.info or {}
        revenue, earnings = _annual_growth(ticker)
        return ticker, info, revenue, earnings
    
    try:
        result = with_rate_limit_retry(fetch, max_retries=3, delay=2.0)
        if result is None:
            return empty
        ticker, info, revenue, earnings = result
    except Exception:
        return empty
    
    if revenue is None:
        revenue = _finite(info.get("revenueGrowth"))
    if earnings is None:
        earnings = _finite(info.get("earningsGrowth"))
    eps = _finite(info.get("trailingEps"))
    pe = _finite(info.get("trailingPE"))
    
    # Métricas de calidad
    operating_margin = _finite(info.get("operatingMargins"))
    net_margin = _finite(info.get("profitMargins"))
    roe = _finite(info.get("returnOnEquity"))
    debt_to_equity = _finite(info.get("debtToEquity"))
    
    # FCF Yield = Free Cash Flow / Market Cap
    fcf = _finite(info.get("freeCashflow"))
    market_cap = _finite(info.get("marketCap"))
    fcf_yield = None
    if fcf is not None and market_cap is not None and market_cap > 0:
        fcf_yield = fcf / market_cap
    
    empty.update(
        {
            "revenue_growth_yoy": revenue,
            "earnings_growth_yoy": earnings,
            "pe": pe,
            "ps": _finite(info.get("priceToSalesTrailing12Months")),
            "ev_ebitda": _finite(info.get("enterpriseToEbitda")),
            "earnings_non_positive": eps is not None and eps <= 0,
            "sector": gics_code(info.get("sector") if isinstance(info.get("sector"), str) else None),
            "operating_margin": operating_margin,
            "net_margin": net_margin,
            "roe": roe,
            "debt_to_equity": debt_to_equity,
            "fcf_yield": fcf_yield,
        }
    )
    return empty


def _fundamentals_useful(facts: dict[str, Any]) -> bool:
    return any(
        facts.get(field) is not None
        for field in (
            "revenue_growth_yoy",
            "earnings_growth_yoy",
            "pe",
            "ps",
            "ev_ebitda",
            "sector",
            "roe",
            "fcf_yield",
        )
    )


def download_fundamentals(
    listings: list[Listing],
    *,
    as_of: str | None = None,
) -> dict[str, dict[str, Any]]:
    facts: dict[str, dict[str, Any]] = {}

    # Filtrar símbolos dados de baja
    active = [item for item in listings if not _is_delisted(item.yahoo_symbol)]
    delisted_count = len(listings) - len(active)

    if delisted_count > 0:
        print(f"omitiendo {delisted_count} símbolos dados de baja en fundamentales", flush=True)
        for item in listings:
            if _is_delisted(item.yahoo_symbol):
                facts[item.yahoo_symbol] = empty_fundamentals()

    pending: list[Listing] = []
    for item in active:
        if as_of:
            cached = ranking_cache.load_fundamentals(as_of, item.yahoo_symbol)
            if cached is not None and _fundamentals_useful(cached):
                facts[item.yahoo_symbol] = cached
                continue
        pending.append(item)
    if as_of and facts:
        print(
            f"fundamentales en caché {len(facts) - delisted_count} de {len(active)}",
            flush=True,
        )

    total = len(pending)
    if total == 0:
        return facts

    with ThreadPoolExecutor(max_workers=FUNDAMENTAL_WORKERS) as pool:
        futures = {pool.submit(read_fundamentals, item.yahoo_symbol): item for item in pending}
        done = 0
        for future in as_completed(futures):
            item = futures[future]
            done += 1
            try:
                result = future.result()
            except Exception:
                result = empty_fundamentals()
            facts[item.yahoo_symbol] = result
            if as_of and _fundamentals_useful(result):
                ranking_cache.save_fundamentals(as_of, item.yahoo_symbol, result)
                ranking_cache.mark_fundamentals_done(as_of, [item.yahoo_symbol])
            if done % 25 == 0 or done == total:
                print(f"fundamentales {done} de {total} pendientes", flush=True)
            time.sleep(FUNDAMENTAL_PAUSE_SECONDS)
    return facts


def bars_from_frame(frame: Any, symbol: str) -> list[dict[str, float | str]]:
    import pandas as pd

    if frame is None:
        return []
    columns = {
        name: _price_series(frame, symbol, name) for name in ("Open", "High", "Low", "Close")
    }
    if any(series is None for series in columns.values()):
        return []
    table = pd.concat(columns, axis=1).dropna()
    bars: list[dict[str, float | str]] = []
    for stamp, row in table.iterrows():
        values = [_finite(row[name]) for name in ("Open", "High", "Low", "Close")]
        if any(value is None for value in values):
            continue
        opened, high, low, close = values
        if stamp is None:
            continue
        day = stamp.date().isoformat() if hasattr(stamp, "date") else str(stamp)[:10]
        bars.append(
            {"time": day, "open": opened, "high": high, "low": low, "close": close}  # type: ignore[dict-item]
        )
    bars.sort(key=lambda bar: str(bar["time"]))
    return bars


_BAR_CACHE: dict[str, tuple[float, list[dict[str, float | str]]]] = {}
_BAR_TTL_SECONDS = 6 * 60 * 60


def daily_bars(yahoo_symbol: str) -> list[dict[str, float | str]]:
    import yfinance as yf

    cached = _BAR_CACHE.get(yahoo_symbol)
    now = time.time()
    if cached and now - cached[0] < _BAR_TTL_SECONDS:
        return cached[1]

    def attempt() -> list[dict[str, float | str]]:
        try:
            frame = yf.download(
                [yahoo_symbol],
                period="1y",
                interval="1d",
                auto_adjust=True,
                progress=False,
                threads=False,
                group_by="ticker",
            )
        except Exception as exc:
            if looks_like_rate_limit(exc):
                raise
            return []
        bars = bars_from_frame(frame, yahoo_symbol)
        if not bars:
            raise RuntimeError(f"empty bars for {yahoo_symbol}")
        return bars

    try:
        bars = call_with_backoff(
            attempt,
            should_retry=lambda exc: looks_like_rate_limit(exc) or "empty bars" in str(exc),
        )
    except Exception:
        bars = []
    _BAR_CACHE[yahoo_symbol] = (time.time(), bars)
    return bars
