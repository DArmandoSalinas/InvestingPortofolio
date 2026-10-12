from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

HORIZON_SESSIONS = 10
STOCK_COMMISSION = 0.001
CRYPTO_COMMISSION = 0.002

WATCHLIST: list[dict[str, str]] = [
    {"asset_class": "stock", "symbol": "AAPL", "yahoo_symbol": "AAPL", "name": "Apple"},
    {"asset_class": "stock", "symbol": "MSFT", "yahoo_symbol": "MSFT", "name": "Microsoft"},
    {"asset_class": "stock", "symbol": "NVDA", "yahoo_symbol": "NVDA", "name": "NVIDIA"},
    {"asset_class": "stock", "symbol": "AMZN", "yahoo_symbol": "AMZN", "name": "Amazon"},
    {"asset_class": "stock", "symbol": "META", "yahoo_symbol": "META", "name": "Meta"},
    {"asset_class": "stock", "symbol": "GOOGL", "yahoo_symbol": "GOOGL", "name": "Alphabet"},
    {"asset_class": "stock", "symbol": "AVGO", "yahoo_symbol": "AVGO", "name": "Broadcom"},
    {"asset_class": "stock", "symbol": "TSLA", "yahoo_symbol": "TSLA", "name": "Tesla"},
    {"asset_class": "stock", "symbol": "AMD", "yahoo_symbol": "AMD", "name": "AMD"},
    {"asset_class": "stock", "symbol": "NFLX", "yahoo_symbol": "NFLX", "name": "Netflix"},
    {"asset_class": "stock", "symbol": "JPM", "yahoo_symbol": "JPM", "name": "JPMorgan"},
    {"asset_class": "stock", "symbol": "LLY", "yahoo_symbol": "LLY", "name": "Eli Lilly"},
    {"asset_class": "stock", "symbol": "XOM", "yahoo_symbol": "XOM", "name": "Exxon Mobil"},
    {"asset_class": "stock", "symbol": "COST", "yahoo_symbol": "COST", "name": "Costco"},
    {"asset_class": "stock", "symbol": "WMT", "yahoo_symbol": "WMT", "name": "Walmart"},
    {"asset_class": "crypto", "symbol": "BTC", "yahoo_symbol": "BTC-USD", "name": "Bitcoin"},
    {"asset_class": "crypto", "symbol": "ETH", "yahoo_symbol": "ETH-USD", "name": "Ethereum"},
]

SPY_SYMBOL = "SPY"
BTC_SYMBOL = "BTC-USD"
NEW_YORK = ZoneInfo("America/New_York")


def completed_bars(
    bars: list[dict[str, Any]],
    asset_class: str,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return [bar for bar in bars if _session_closed(str(bar.get("time"))[:10], asset_class, moment)]


def _session_closed(day: str, asset_class: str, now: datetime) -> bool:
    if len(day) != 10:
        return False
    session = date.fromisoformat(day)
    if asset_class == "crypto":
        close_at = datetime(session.year, session.month, session.day, tzinfo=timezone.utc) + timedelta(days=1)
    else:
        close_at = datetime.combine(session, time(16, 0), tzinfo=NEW_YORK)
    return now >= close_at


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _pct(value: float) -> str:
    return f"{value * 100:.1f}".replace(".", ",") + "%"


def _px(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _closes(bars: list[dict[str, Any]]) -> list[float] | None:
    closes: list[float] = []
    for bar in bars:
        close = _number(bar.get("close"))
        high = _number(bar.get("high"))
        low = _number(bar.get("low"))
        if close is None or high is None or low is None or close <= 0:
            return None
        closes.append(close)
    return closes


def confidence_of(setup: str, return_20: float, sma_gap: float) -> int:
    score = 65 if setup == "impulso" else 50
    if 0 < return_20 <= 0.12:
        score += 15
    elif return_20 > 0.12:
        score += 5
    if 0 < sma_gap <= 0.06:
        score += 15
    elif sma_gap > 0.06:
        score += 5
    return max(0, min(100, score))


def propose(
    bars: list[dict[str, Any]],
    asset_class: str,
    *,
    stock_commission: float = STOCK_COMMISSION,
    crypto_commission: float = CRYPTO_COMMISSION,
    horizon_sessions: int = HORIZON_SESSIONS,
) -> dict[str, Any] | None:
    if len(bars) < 51:
        return None
    closes = _closes(bars)
    if closes is None:
        return None
    sma20 = _mean(closes[-20:])
    sma50 = _mean(closes[-50:])
    previous = closes[-21]
    if sma20 is None or sma50 is None or sma20 <= 0 or sma50 <= 0 or previous == 0:
        return None
    last = bars[-1]
    close = closes[-1]
    return_20 = close / previous - 1
    sma_gap = (sma20 - sma50) / sma50
    high_20 = max(_number(bar["high"]) or 0 for bar in bars[-20:])
    low_10 = min(_number(bar["low"]) or close for bar in bars[-10:])
    near_high = close >= high_20 * 0.98
    stacked = close > sma20 > sma50 and return_20 > 0 and near_high
    pullback = (
        sma20 > sma50
        and close > sma50
        and abs(close - sma20) / sma20 <= 0.015
        and return_20 > 0
        and not near_high
    )
    if stacked:
        setup = "impulso"
        setup_reason = "El cierre está cerca del máximo de 20 sesiones."
    elif pullback:
        setup = "retroceso"
        setup_reason = "El cierre volvió a la media de 20 sin perder la de 50."
    else:
        return None

    stop = min(low_10, sma20)
    if stop >= close:
        return None
    target = close + 2 * (close - stop)
    commission = crypto_commission if asset_class == "crypto" else stock_commission
    return {
        "as_of": str(last["time"])[:10],
        "setup": setup,
        "entry": close,
        "stop": stop,
        "target": target,
        "confidence": confidence_of(setup, return_20, sma_gap),
        "horizon_sessions": horizon_sessions,
        "commission_rate": commission,
        "reasons": [
            "El cierre está sobre la media de 20 y esa media está sobre la de 50."
            if setup == "impulso"
            else "La media de 20 sigue sobre la de 50.",
            f"En 20 sesiones el precio cambió {_pct(return_20)}.",
            setup_reason,
            f"La entrada es el cierre, {_px(close)}. El stop queda en {_px(stop)} y el objetivo en {_px(target)}.",
        ],
        "risks": [
            "Si en un mismo día el precio toca el stop y el objetivo, la señal se cierra en el stop.",
            "Al cerrar se descuenta la comisión de ida y vuelta.",
        ],
    }


def scoreboard(rows: list[dict[str, Any]]) -> dict[str, Any]:
    closed = [row for row in rows if row.get("status") != "open"]

    def numbers(key: str) -> list[float]:
        values: list[float] = []
        for row in closed:
            number = _number(row.get(key))
            if number is not None:
                values.append(number)
        return values

    targets = sum(1 for row in closed if row.get("status") == "target")
    nets = numbers("net_return")
    spies = numbers("spy_return")
    btcs = numbers("btc_return")
    return {
        "open": sum(1 for row in rows if row.get("status") == "open"),
        "closed": len(closed),
        "targets": targets,
        "stops": sum(1 for row in closed if row.get("status") == "stop"),
        "expired": sum(1 for row in closed if row.get("status") == "expired"),
        "hit_rate": None if not closed else targets / len(closed),
        "net_return": None if not nets else sum(nets) / len(nets),
        "spy_return": None if not spies else sum(spies) / len(spies),
        "btc_return": None if not btcs else sum(btcs) / len(btcs),
        "net_count": len(nets),
        "spy_count": len(spies),
        "btc_count": len(btcs),
    }


def buy_hold(bars: list[dict[str, Any]], start: str, end: str) -> float | None:
    closes = {str(bar.get("time"))[:10]: _number(bar.get("close")) for bar in bars}
    first = closes.get(start)
    last = closes.get(end)
    if first is None or last is None or first == 0:
        return None
    return last / first - 1


def evaluate(
    entry: float,
    stop: float,
    target: float,
    future: list[dict[str, Any]],
    horizon: int,
    commission: float,
) -> dict[str, Any] | None:
    if horizon < 1 or entry <= 0 or not future:
        return None
    window = future[:horizon]
    outcome: dict[str, Any] | None = None
    for bar in window:
        high = _number(bar.get("high"))
        low = _number(bar.get("low"))
        close = _number(bar.get("close"))
        if high is None or low is None or close is None:
            return None
        hit_stop = low <= stop
        hit_target = high >= target
        day = str(bar.get("time"))[:10]
        if hit_stop:
            outcome = {"status": "stop", "exit_price": stop, "exit_as_of": day}
            break
        if hit_target:
            outcome = {"status": "target", "exit_price": target, "exit_as_of": day}
            break
    if outcome is None:
        if len(future) < horizon:
            return None
        last = window[-1]
        close = _number(last.get("close"))
        if close is None:
            return None
        outcome = {
            "status": "expired",
            "exit_price": close,
            "exit_as_of": str(last.get("time"))[:10],
        }
    gross = outcome["exit_price"] / entry - 1
    outcome["gross_return"] = gross
    outcome["net_return"] = gross - commission
    return outcome
