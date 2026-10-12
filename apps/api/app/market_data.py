import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.universe import Listing, gics_code

PRICE_CHUNK = 40
FUNDAMENTAL_WORKERS = 6


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


def download_closes(symbols: list[str]) -> dict[str, list[float]]:
    closes: dict[str, list[float]] = {}
    unique = list(dict.fromkeys(symbols))
    for start in range(0, len(unique), PRICE_CHUNK):
        chunk = unique[start : start + PRICE_CHUNK]
        print(f"precios {start + 1}-{start + len(chunk)} de {len(unique)}", flush=True)
        closes.update(_download_chunk(chunk))
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


def empty_fundamentals() -> dict[str, Any]:
    return {
        "revenue_growth_yoy": None,
        "earnings_growth_yoy": None,
        "pe": None,
        "ps": None,
        "ev_ebitda": None,
        "earnings_non_positive": False,
        "sector": None,
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
    empty.update(
        {
            "revenue_growth_yoy": revenue,
            "earnings_growth_yoy": earnings,
            "pe": pe,
            "ps": _finite(info.get("priceToSalesTrailing12Months")),
            "ev_ebitda": _finite(info.get("enterpriseToEbitda")),
            "earnings_non_positive": eps is not None and eps <= 0,
            "sector": gics_code(info.get("sector") if isinstance(info.get("sector"), str) else None),
        }
    )
    return empty


def download_fundamentals(listings: list[Listing]) -> dict[str, dict[str, Any]]:
    facts: dict[str, dict[str, Any]] = {}
    total = len(listings)
    with ThreadPoolExecutor(max_workers=FUNDAMENTAL_WORKERS) as pool:
        futures = {pool.submit(read_fundamentals, item.yahoo_symbol): item for item in listings}
        done = 0
        for future in as_completed(futures):
            item = futures[future]
            done += 1
            try:
                facts[item.yahoo_symbol] = future.result()
            except Exception:
                facts[item.yahoo_symbol] = empty_fundamentals()
            if done % 25 == 0 or done == total:
                print(f"fundamentales {done} de {total}", flush=True)
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
    import time

    import yfinance as yf

    cached = _BAR_CACHE.get(yahoo_symbol)
    now = time.time()
    if cached and now - cached[0] < _BAR_TTL_SECONDS:
        return cached[1]
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
        bars = bars_from_frame(frame, yahoo_symbol)
    except Exception:
        bars = []
    _BAR_CACHE[yahoo_symbol] = (now, bars)
    return bars
