from datetime import datetime
from typing import Any

from app.analyst import signal_context
from app.config import get_settings
from app.db import SupabaseRest
from app.market_data import daily_bars
from app.refresh_ranking import MONTERREY
from app.signals import (
    BTC_SYMBOL,
    CRYPTO_COMMISSION,
    HORIZON_SESSIONS,
    SPY_SYMBOL,
    STOCK_COMMISSION,
    WATCHLIST,
    buy_hold,
    completed_bars,
    evaluate,
    propose,
)


def _float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _after(bars: list[dict[str, Any]], as_of: str) -> list[dict[str, Any]]:
    return [bar for bar in bars if str(bar.get("time"))[:10] > as_of]


def refresh_signals() -> None:
    settings = get_settings()
    db = SupabaseRest(settings)
    try:
        stored = db.list_signals()
        config = db.get_signal_config() or {}
        stock_commission = float(config.get("stock_commission") or STOCK_COMMISSION)
        crypto_commission = float(config.get("crypto_commission") or CRYPTO_COMMISSION)
        configured_horizon = int(config.get("horizon_sessions") or HORIZON_SESSIONS)
        listed = [item for item in db.list_watchlist() if item.get("active")]
        universe = listed or WATCHLIST
        needed = {item["yahoo_symbol"] for item in universe}
        needed.update({SPY_SYMBOL, BTC_SYMBOL})
        classes = {item["yahoo_symbol"]: item["asset_class"] for item in universe}
        classes[SPY_SYMBOL] = "stock"
        classes[BTC_SYMBOL] = "crypto"
        for row in stored:
            needed.add(row["yahoo_symbol"])
            classes.setdefault(row["yahoo_symbol"], str(row.get("asset_class") or "stock"))
        prices = {
            symbol: completed_bars(daily_bars(symbol), classes.get(symbol, "stock"))
            for symbol in sorted(needed)
        }
        spy = prices.get(SPY_SYMBOL) or []
        btc = prices.get(BTC_SYMBOL) or []
        for row in stored:
            if row.get("status") != "open":
                continue
            entry = _float(row.get("entry"))
            stop = _float(row.get("stop"))
            target = _float(row.get("target"))
            commission = _float(row.get("commission_rate"))
            horizon = int(row.get("horizon_sessions") or 0)
            if entry is None or stop is None or target is None or commission is None:
                continue
            outcome = evaluate(
                entry,
                stop,
                target,
                _after(prices.get(row["yahoo_symbol"]) or [], str(row["as_of"])),
                horizon,
                commission,
            )
            if outcome is None:
                continue
            outcome["spy_return"] = buy_hold(spy, str(row["as_of"]), outcome["exit_as_of"])
            outcome["btc_return"] = buy_hold(btc, str(row["as_of"]), outcome["exit_as_of"])
            db.update_signal(row["id"], outcome)
            print(f"señal {row['symbol']} {outcome['status']}", flush=True)

        open_symbols = {row["yahoo_symbol"] for row in stored if row.get("status") == "open"}
        created: list[dict[str, Any]] = []
        for item in universe:
            if item["yahoo_symbol"] in open_symbols:
                continue
            draft = propose(
                prices.get(item["yahoo_symbol"]) or [],
                item["asset_class"],
                stock_commission=stock_commission,
                crypto_commission=crypto_commission,
                horizon_sessions=configured_horizon,
            )
            if draft is None:
                continue
            note = signal_context(
                settings.xai_api_key,
                {**item, **draft},
            )
            created.append(
                {
                    "as_of": draft["as_of"],
                    "asset_class": item["asset_class"],
                    "symbol": item["symbol"],
                    "yahoo_symbol": item["yahoo_symbol"],
                    "name": item["name"],
                    "setup": draft["setup"],
                    "entry": draft["entry"],
                    "stop": draft["stop"],
                    "target": draft["target"],
                    "confidence": draft["confidence"],
                    "reasons": draft["reasons"],
                    "risks": draft["risks"],
                    "horizon_sessions": draft["horizon_sessions"],
                    "commission_rate": draft["commission_rate"],
                    "status": "open",
                    "context_note": note,
                }
            )
        db.insert_signals(created)
        print(
            f"señales {datetime.now(MONTERREY).date().isoformat()}: {len(created)} nuevas",
            flush=True,
        )
        
        # Actualizar métricas de desempeño por tipo de señal
        _update_performance_metrics(db)
        
    finally:
        db.close()


def _update_performance_metrics(db: SupabaseRest) -> None:
    """
    Calcula y actualiza las métricas de desempeño por tipo de señal.
    
    Args:
        db: Conexión a la base de datos
    """
    all_signals = db.list_signals()
    
    # Agrupar por setup
    by_setup: dict[str, list[dict[str, Any]]] = {"impulso": [], "retroceso": []}
    
    for signal in all_signals:
        setup = signal.get("setup")
        if setup in by_setup:
            by_setup[setup].append(signal)
    
    # Calcular métricas para cada tipo
    for setup, signals in by_setup.items():
        closed = [s for s in signals if s.get("status") != "open"]
        
        if not closed:
            continue
        
        targets = sum(1 for s in closed if s.get("status") == "target")
        stops = sum(1 for s in closed if s.get("status") == "stop")
        expired = sum(1 for s in closed if s.get("status") == "expired")
        
        net_returns = [_float(s.get("net_return")) for s in closed if _float(s.get("net_return")) is not None]
        gross_returns = [_float(s.get("gross_return")) for s in closed if _float(s.get("gross_return")) is not None]
        
        winners = [r for r in net_returns if r > 0]
        losers = [r for r in net_returns if r <= 0]
        
        metrics = {
            "setup": setup,
            "total_signals": len(closed),
            "targets": targets,
            "stops": stops,
            "expired": expired,
            "hit_rate": targets / len(closed) if closed else None,
            "avg_net_return": sum(net_returns) / len(net_returns) if net_returns else None,
            "avg_gross_return": sum(gross_returns) / len(gross_returns) if gross_returns else None,
            "avg_winner": sum(winners) / len(winners) if winners else None,
            "avg_loser": sum(losers) / len(losers) if losers else None,
            "win_loss_ratio": (
                (sum(winners) / len(winners)) / abs(sum(losers) / len(losers))
                if winners and losers and sum(losers) != 0
                else None
            ),
        }
        
        db.upsert_performance(metrics)
        print(f"métricas {setup}: {len(closed)} señales, {targets} objetivos", flush=True)
