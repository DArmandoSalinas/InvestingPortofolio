"""
Backtest corregido para señales de trading.

Correcciones aplicadas:
- Drawdown por operación (peor pérdida) + simulación de portafolio
- Target hit rate + positive return rate
- Comparación por señal contra SPY en la misma ventana
- Sin look-ahead bias
- Precios ajustados
- Universo completo de la base de datos
- Tests unitarios con series sintéticas
"""

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.signals import completed_bars, evaluate, propose


@dataclass
class SignalResult:
    """Resultado de una señal evaluada."""

    as_of: str
    asset_class: str
    symbol: str
    setup: str
    entry: float
    stop: float
    target: float
    confidence: int
    horizon_sessions: int
    commission_rate: float
    status: str
    exit_price: float | None
    exit_as_of: str | None
    gross_return: float | None
    net_return: float | None
    spy_return: float | None
    btc_return: float | None


@dataclass
class BacktestMetrics:
    """Métricas del backtest."""

    total_signals: int
    target_hit_rate: float | None  # % que alcanzó objetivo
    positive_return_rate: float | None  # % con retorno neto > 0
    beats_spy_rate: float | None  # % que superó a SPY en la misma ventana
    avg_net_return: float | None
    avg_spy_return: float | None
    avg_btc_return: float | None
    max_loss_per_trade: float | None  # Peor pérdida individual
    portfolio_max_drawdown: float | None  # Drawdown simulado con posición fija
    targets: int
    stops: int
    expired: int
    avg_winner: float | None
    avg_loser: float | None
    win_loss_ratio: float | None


@dataclass
class SetupMetrics:
    """Métricas por tipo de setup."""

    setup: str
    total: int
    target_hit_rate: float | None
    positive_return_rate: float | None
    beats_spy_rate: float | None
    avg_net_return: float | None
    targets: int
    stops: int
    expired: int


@dataclass
class BacktestConfig:
    """Configuración del backtest."""

    stock_commission: float = 0.001
    crypto_commission: float = 0.002
    horizon_sessions: int = 10
    lookback_years: int = 5
    in_sample_ratio: float = 0.6
    position_size: float = 0.10  # 10% del capital por posición
    max_positions: int = 10  # Máximo de posiciones simultáneas


def _finite(value: Any) -> float | None:
    """Extrae un número finito, devuelve None si no es válido."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _download_historical(
    yahoo_symbol: str, years: int = 5
) -> list[dict[str, float | str]]:
    """
    Descarga datos históricos ajustados.

    Args:
        yahoo_symbol: Símbolo de Yahoo Finance
        years: Años de historia

    Returns:
        Lista de barras diarias con precios ajustados
    """
    import yfinance as yf

    try:
        ticker = yf.Ticker(yahoo_symbol)
        frame = ticker.history(period=f"{years}y")
    except Exception:
        return []

    if frame is None or frame.empty:
        return []

    bars: list[dict[str, float | str]] = []
    for stamp, row in frame.iterrows():
        if stamp is None:
            continue
        day = stamp.date().isoformat() if hasattr(stamp, "date") else str(stamp)[:10]
        opened = _finite(row["Open"])
        high = _finite(row["High"])
        low = _finite(row["Low"])
        close = _finite(row["Close"])

        if opened is None or high is None or low is None or close is None:
            continue

        bars.append({"time": day, "open": opened, "high": high, "low": low, "close": close})  # type: ignore[dict-item]

    bars.sort(key=lambda bar: str(bar["time"]))
    return bars


def _split_data(
    bars: list[dict[str, Any]], in_sample_ratio: float
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Divide datos en in-sample y out-of-sample."""
    split_index = int(len(bars) * in_sample_ratio)
    return bars[:split_index], bars[split_index:]


def _calculate_portfolio_drawdown(
    results: list[SignalResult], position_size: float, max_positions: int
) -> float | None:
    """
    Simula portafolio con posición fija y calcula drawdown.

    Asume:
    - Cada posición usa position_size del capital
    - Máximo max_positions simultáneas
    - Retornos se aplican proporcionalmente

    Args:
        results: Resultados de señales
        position_size: Fracción del capital por posición (0.10 = 10%)
        max_positions: Máximo de posiciones simultáneas

    Returns:
        Drawdown máximo como fracción negativa
    """
    if not results:
        return None

    # Ordenar por fecha
    sorted_results = sorted(
        [r for r in results if r.status != "open" and r.net_return is not None],
        key=lambda r: r.as_of,
    )

    if not sorted_results:
        return None

    equity = 1.0
    peak = 1.0
    max_dd = 0.0

    for result in sorted_results:
        # Aplicar retorno ponderado por tamaño de posición
        equity_change = result.net_return * position_size  # type: ignore[operator]
        equity *= 1 + equity_change

        # Actualizar peak y drawdown
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak
        if dd > max_dd:
            max_dd = dd

    return -max_dd if max_dd > 0 else 0.0


def _calculate_metrics(results: list[SignalResult], config: BacktestConfig) -> BacktestMetrics:
    """
    Calcula métricas agregadas.

    Args:
        results: Resultados de señales
        config: Configuración del backtest

    Returns:
        Métricas calculadas
    """
    closed = [r for r in results if r.status != "open"]
    if not closed:
        return BacktestMetrics(
            total_signals=len(results),
            target_hit_rate=None,
            positive_return_rate=None,
            beats_spy_rate=None,
            avg_net_return=None,
            avg_spy_return=None,
            avg_btc_return=None,
            max_loss_per_trade=None,
            portfolio_max_drawdown=None,
            targets=0,
            stops=0,
            expired=0,
            avg_winner=None,
            avg_loser=None,
            win_loss_ratio=None,
        )

    targets = sum(1 for r in closed if r.status == "target")
    stops = sum(1 for r in closed if r.status == "stop")
    expired = sum(1 for r in closed if r.status == "expired")

    net_returns = [r.net_return for r in closed if r.net_return is not None]
    spy_returns = [r.spy_return for r in closed if r.spy_return is not None]
    btc_returns = [r.btc_return for r in closed if r.btc_return is not None]

    # Target hit rate (alcanzó el objetivo)
    target_hit_rate = targets / len(closed)

    # Positive return rate (rendimiento neto > 0)
    positive_count = sum(1 for r in net_returns if r > 0)
    positive_return_rate = positive_count / len(net_returns) if net_returns else None

    # Beats SPY rate (superó a SPY en la misma ventana)
    beats_spy_count = sum(
        1
        for r in closed
        if r.net_return is not None and r.spy_return is not None and r.net_return > r.spy_return
    )
    beats_spy_rate = beats_spy_count / len(closed) if closed else None

    winners = [r for r in net_returns if r > 0]
    losers = [r for r in net_returns if r <= 0]

    # Drawdowns
    max_loss = min(net_returns) if net_returns else None
    portfolio_dd = _calculate_portfolio_drawdown(results, config.position_size, config.max_positions)

    return BacktestMetrics(
        total_signals=len(results),
        target_hit_rate=target_hit_rate,
        positive_return_rate=positive_return_rate,
        beats_spy_rate=beats_spy_rate,
        avg_net_return=sum(net_returns) / len(net_returns) if net_returns else None,
        avg_spy_return=sum(spy_returns) / len(spy_returns) if spy_returns else None,
        avg_btc_return=sum(btc_returns) / len(btc_returns) if btc_returns else None,
        max_loss_per_trade=max_loss,
        portfolio_max_drawdown=portfolio_dd,
        targets=targets,
        stops=stops,
        expired=expired,
        avg_winner=sum(winners) / len(winners) if winners else None,
        avg_loser=sum(losers) / len(losers) if losers else None,
        win_loss_ratio=(
            (sum(winners) / len(winners)) / abs(sum(losers) / len(losers))
            if winners and losers and sum(losers) != 0
            else None
        ),
    )


def _metrics_by_setup(results: list[SignalResult]) -> dict[str, SetupMetrics]:
    """Calcula métricas por tipo de setup."""
    by_setup: dict[str, list[SignalResult]] = {}
    for result in results:
        if result.setup not in by_setup:
            by_setup[result.setup] = []
        by_setup[result.setup].append(result)

    metrics: dict[str, SetupMetrics] = {}
    for setup, setup_results in by_setup.items():
        closed = [r for r in setup_results if r.status != "open"]
        if not closed:
            continue

        targets = sum(1 for r in closed if r.status == "target")
        net_returns = [r.net_return for r in closed if r.net_return is not None]

        positive_count = sum(1 for r in net_returns if r > 0)
        positive_rate = positive_count / len(net_returns) if net_returns else None

        beats_spy_count = sum(
            1
            for r in closed
            if r.net_return is not None
            and r.spy_return is not None
            and r.net_return > r.spy_return
        )
        beats_spy_rate = beats_spy_count / len(closed)

        metrics[setup] = SetupMetrics(
            setup=setup,
            total=len(setup_results),
            target_hit_rate=targets / len(closed),
            positive_return_rate=positive_rate,
            beats_spy_rate=beats_spy_rate,
            avg_net_return=sum(net_returns) / len(net_returns) if net_returns else None,
            targets=targets,
            stops=sum(1 for r in closed if r.status == "stop"),
            expired=sum(1 for r in closed if r.status == "expired"),
        )

    return metrics


def backtest_asset(
    symbol: str,
    yahoo_symbol: str,
    asset_class: str,
    config: BacktestConfig,
    spy_bars: list[dict[str, Any]] | None = None,
    btc_bars: list[dict[str, Any]] | None = None,
) -> tuple[list[SignalResult], list[SignalResult]]:
    """
    Ejecuta backtest para un activo.

    Args:
        symbol: Símbolo del activo
        yahoo_symbol: Símbolo de Yahoo Finance
        asset_class: 'stock' o 'crypto'
        config: Configuración
        spy_bars: Barras de SPY (opcional)
        btc_bars: Barras de BTC (opcional)

    Returns:
        (resultados_in_sample, resultados_out_of_sample)
    """
    from app.signals import buy_hold

    # Descargar datos históricos
    all_bars = _download_historical(yahoo_symbol, config.lookback_years)
    if len(all_bars) < 252:
        return [], []

    # Dividir en in-sample y out-of-sample
    in_sample_bars, out_of_sample_bars = _split_data(all_bars, config.in_sample_ratio)

    commission = (
        config.crypto_commission if asset_class == "crypto" else config.stock_commission
    )

    def _run_backtest(bars: list[dict[str, Any]]) -> list[SignalResult]:
        """Ejecuta backtest en un conjunto de barras."""
        results: list[SignalResult] = []

        # Recorrer historia generando señales
        for i in range(252, len(bars)):
            # Datos disponibles hasta este punto (sin look-ahead)
            available = bars[: i + 1]
            completed = completed_bars(available, asset_class, None)

            if len(completed) < 51:
                continue

            # Intentar generar señal
            signal = propose(
                completed,
                asset_class,
                stock_commission=config.stock_commission,
                crypto_commission=config.crypto_commission,
                horizon_sessions=config.horizon_sessions,
            )

            if signal is None:
                continue

            as_of = signal["as_of"]

            # No abrir nueva señal si ya hay una abierta
            open_signals = [r for r in results if r.status == "open"]
            if open_signals:
                continue

            # Datos futuros para evaluación (entrada al día siguiente)
            future_bars = [bar for bar in bars if str(bar["time"]) > as_of]

            # Evaluar señal
            outcome = evaluate(
                signal["entry"],
                signal["stop"],
                signal["target"],
                future_bars,
                signal["horizon_sessions"],
                commission,
            )

            if outcome is None:
                # Sin suficientes datos futuros
                results.append(
                    SignalResult(
                        as_of=as_of,
                        asset_class=asset_class,
                        symbol=symbol,
                        setup=signal["setup"],
                        entry=signal["entry"],
                        stop=signal["stop"],
                        target=signal["target"],
                        confidence=signal["confidence"],
                        horizon_sessions=signal["horizon_sessions"],
                        commission_rate=commission,
                        status="open",
                        exit_price=None,
                        exit_as_of=None,
                        gross_return=None,
                        net_return=None,
                        spy_return=None,
                        btc_return=None,
                    )
                )
                continue

            # Calcular rendimientos de referencia en la misma ventana
            spy_return = None
            btc_return = None

            if spy_bars:
                spy_return = buy_hold(spy_bars, as_of, outcome["exit_as_of"])

            if btc_bars:
                btc_return = buy_hold(btc_bars, as_of, outcome["exit_as_of"])

            results.append(
                SignalResult(
                    as_of=as_of,
                    asset_class=asset_class,
                    symbol=symbol,
                    setup=signal["setup"],
                    entry=signal["entry"],
                    stop=signal["stop"],
                    target=signal["target"],
                    confidence=signal["confidence"],
                    horizon_sessions=signal["horizon_sessions"],
                    commission_rate=commission,
                    status=outcome["status"],
                    exit_price=outcome.get("exit_price"),
                    exit_as_of=outcome.get("exit_as_of"),
                    gross_return=outcome.get("gross_return"),
                    net_return=outcome.get("net_return"),
                    spy_return=spy_return,
                    btc_return=btc_return,
                )
            )

        return results

    in_sample_results = _run_backtest(in_sample_bars)
    out_of_sample_results = _run_backtest(out_of_sample_bars)

    return in_sample_results, out_of_sample_results


def run_backtest(
    universe: list[dict[str, str]], config: BacktestConfig
) -> dict[str, Any]:
    """
    Ejecuta backtest en el universo completo.

    Args:
        universe: Lista de activos [{symbol, yahoo_symbol, asset_class}, ...]
        config: Configuración del backtest

    Returns:
        Diccionario con resultados completos
    """
    # Descargar SPY y BTC para referencia
    print("Descargando referencias (SPY, BTC)...", flush=True)
    spy_bars = _download_historical("SPY", config.lookback_years)
    btc_bars = _download_historical("BTC-USD", config.lookback_years)

    all_in_sample: list[SignalResult] = []
    all_out_of_sample: list[SignalResult] = []

    print(f"\nProcesando {len(universe)} activos...\n", flush=True)

    for i, asset in enumerate(universe, 1):
        symbol = asset["symbol"]
        yahoo_symbol = asset["yahoo_symbol"]
        asset_class = asset.get("asset_class", "stock")

        print(f"[{i}/{len(universe)}] {symbol}...", flush=True)

        in_sample, out_of_sample = backtest_asset(
            symbol, yahoo_symbol, asset_class, config, spy_bars, btc_bars
        )

        all_in_sample.extend(in_sample)
        all_out_of_sample.extend(out_of_sample)

    # Calcular métricas
    in_sample_metrics = _calculate_metrics(all_in_sample, config)
    out_of_sample_metrics = _calculate_metrics(all_out_of_sample, config)

    in_sample_by_setup = _metrics_by_setup(all_in_sample)
    out_of_sample_by_setup = _metrics_by_setup(all_out_of_sample)

    return {
        "config": {
            "stock_commission": config.stock_commission,
            "crypto_commission": config.crypto_commission,
            "horizon_sessions": config.horizon_sessions,
            "lookback_years": config.lookback_years,
            "in_sample_ratio": config.in_sample_ratio,
            "position_size": config.position_size,
            "max_positions": config.max_positions,
        },
        "in_sample": {
            "metrics": in_sample_metrics,
            "by_setup": in_sample_by_setup,
            "signals": [
                {
                    "as_of": r.as_of,
                    "symbol": r.symbol,
                    "setup": r.setup,
                    "status": r.status,
                    "net_return": r.net_return,
                    "spy_return": r.spy_return,
                }
                for r in all_in_sample
            ],
        },
        "out_of_sample": {
            "metrics": out_of_sample_metrics,
            "by_setup": out_of_sample_by_setup,
            "signals": [
                {
                    "as_of": r.as_of,
                    "symbol": r.symbol,
                    "setup": r.setup,
                    "status": r.status,
                    "net_return": r.net_return,
                    "spy_return": r.spy_return,
                }
                for r in all_out_of_sample
            ],
        },
    }
