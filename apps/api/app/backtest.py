"""
Sistema de backtest reproducible para validar reglas de señales.

El backtest descarga datos históricos y aplica las reglas de señales
retrospectivamente. Evalúa cada señal con comisiones y la regla de que
si stop y objetivo caen el mismo día, cuenta el stop.

Divide los datos en in-sample y out-of-sample para evitar sobreajuste.
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.signals import (
    CRYPTO_COMMISSION,
    HORIZON_SESSIONS,
    STOCK_COMMISSION,
    completed_bars,
    evaluate,
    propose,
)


@dataclass
class BacktestConfig:
    """Configuración del backtest."""

    stock_commission: float = STOCK_COMMISSION
    crypto_commission: float = CRYPTO_COMMISSION
    horizon_sessions: int = HORIZON_SESSIONS
    lookback_years: int = 5  # Años de historia para el backtest
    in_sample_ratio: float = 0.6  # 60% para entrenamiento, 40% para validación


@dataclass
class SignalResult:
    """Resultado de una señal en el backtest."""

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
    hit_rate: float | None  # Porcentaje de señales que llegaron al objetivo
    avg_net_return: float | None  # Rendimiento neto promedio
    avg_spy_return: float | None  # Rendimiento promedio de SPY en el mismo periodo
    avg_btc_return: float | None  # Rendimiento promedio de BTC en el mismo periodo
    max_drawdown: float | None  # Máxima caída acumulada
    targets: int  # Señales que llegaron al objetivo
    stops: int  # Señales que tocaron el stop
    expired: int  # Señales que expiraron
    avg_winner: float | None  # Rendimiento promedio de las ganadoras
    avg_loser: float | None  # Rendimiento promedio de las perdedoras
    win_loss_ratio: float | None  # Ratio ganancia promedio / pérdida promedia


@dataclass
class SetupMetrics:
    """Métricas por tipo de setup (impulso vs retroceso)."""

    setup: str
    total: int
    hit_rate: float | None
    avg_net_return: float | None
    targets: int
    stops: int
    expired: int


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
    Descarga datos históricos para backtest.

    Args:
        yahoo_symbol: Símbolo de Yahoo Finance
        years: Años de historia a descargar

    Returns:
        Lista de barras diarias ordenadas por fecha
    """
    import yfinance as yf

    try:
        frame = yf.download(
            [yahoo_symbol],
            period=f"{years}y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )
    except Exception:
        return []

    if frame is None or frame.empty:
        return []

    bars: list[dict[str, float | str]] = []
    for stamp, row in frame.iterrows():
        if stamp is None:
            continue
        day = stamp.date().isoformat() if hasattr(stamp, "date") else str(stamp)[:10]
        opened = _finite(row.get("Open"))
        high = _finite(row.get("High"))
        low = _finite(row.get("Low"))
        close = _finite(row.get("Close"))

        if opened is None or high is None or low is None or close is None:
            continue

        bars.append({"time": day, "open": opened, "high": high, "low": low, "close": close})  # type: ignore[dict-item]

    bars.sort(key=lambda bar: str(bar["time"]))
    return bars


def _split_data(
    bars: list[dict[str, Any]], ratio: float = 0.6
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Divide los datos en in-sample y out-of-sample.

    Args:
        bars: Datos históricos
        ratio: Proporción para in-sample (default 0.6 = 60%)

    Returns:
        Tupla (in_sample, out_of_sample)
    """
    split_point = int(len(bars) * ratio)
    return bars[:split_point], bars[split_point:]


def _calculate_drawdown(cumulative_returns: list[float]) -> float | None:
    """
    Calcula el máximo drawdown de una serie de rendimientos acumulados.

    Args:
        cumulative_returns: Lista de rendimientos acumulados (1.0 = sin cambio)

    Returns:
        Máximo drawdown como fracción negativa, o None si no hay datos
    """
    if not cumulative_returns:
        return None

    max_dd = 0.0
    peak = cumulative_returns[0]

    for value in cumulative_returns:
        if value > peak:
            peak = value
        dd = (value - peak) / peak if peak > 0 else 0
        if dd < max_dd:
            max_dd = dd

    return max_dd if max_dd < 0 else 0.0


def _metrics_from_results(
    results: list[SignalResult],
) -> BacktestMetrics:
    """
    Calcula métricas agregadas de un conjunto de resultados.

    Args:
        results: Lista de resultados de señales

    Returns:
        Métricas del backtest
    """
    closed = [r for r in results if r.status != "open"]
    targets = sum(1 for r in closed if r.status == "target")
    stops = sum(1 for r in closed if r.status == "stop")
    expired = sum(1 for r in closed if r.status == "expired")

    net_returns = [r.net_return for r in closed if r.net_return is not None]
    spy_returns = [r.spy_return for r in closed if r.spy_return is not None]
    btc_returns = [r.btc_return for r in closed if r.btc_return is not None]

    winners = [r.net_return for r in closed if r.net_return is not None and r.net_return > 0]
    losers = [r.net_return for r in closed if r.net_return is not None and r.net_return <= 0]

    # Calcular rendimientos acumulados para drawdown
    cumulative = []
    equity = 1.0
    for ret in net_returns:
        equity *= 1 + ret
        cumulative.append(equity)

    return BacktestMetrics(
        total_signals=len(results),
        hit_rate=targets / len(closed) if closed else None,
        avg_net_return=sum(net_returns) / len(net_returns) if net_returns else None,
        avg_spy_return=sum(spy_returns) / len(spy_returns) if spy_returns else None,
        avg_btc_return=sum(btc_returns) / len(btc_returns) if btc_returns else None,
        max_drawdown=_calculate_drawdown(cumulative),
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
    """
    Calcula métricas separadas por tipo de setup.

    Args:
        results: Lista de resultados de señales

    Returns:
        Diccionario con métricas por setup
    """
    by_setup: dict[str, list[SignalResult]] = {}
    for result in results:
        if result.setup not in by_setup:
            by_setup[result.setup] = []
        by_setup[result.setup].append(result)

    metrics: dict[str, SetupMetrics] = {}
    for setup, setup_results in by_setup.items():
        closed = [r for r in setup_results if r.status != "open"]
        targets = sum(1 for r in closed if r.status == "target")
        net_returns = [r.net_return for r in closed if r.net_return is not None]

        metrics[setup] = SetupMetrics(
            setup=setup,
            total=len(setup_results),
            hit_rate=targets / len(closed) if closed else None,
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
    now: datetime | None = None,
) -> tuple[list[SignalResult], list[SignalResult]]:
    """
    Ejecuta el backtest para un activo.

    Args:
        symbol: Símbolo del activo
        yahoo_symbol: Símbolo para Yahoo Finance
        asset_class: 'stock' o 'crypto'
        config: Configuración del backtest
        spy_bars: Barras de SPY para comparación (opcional)
        btc_bars: Barras de BTC para comparación (opcional)
        now: Momento actual para completed_bars (opcional)

    Returns:
        Tupla (resultados_in_sample, resultados_out_of_sample)
    """
    from app.signals import buy_hold

    # Descargar datos históricos
    all_bars = _download_historical(yahoo_symbol, config.lookback_years)
    if len(all_bars) < 252:  # Necesitamos al menos 1 año de datos
        return [], []

    # Dividir en in-sample y out-of-sample
    in_sample_bars, out_of_sample_bars = _split_data(all_bars, config.in_sample_ratio)

    commission = (
        config.crypto_commission if asset_class == "crypto" else config.stock_commission
    )

    def _run_backtest(bars: list[dict[str, Any]]) -> list[SignalResult]:
        """Ejecuta el backtest en un conjunto de datos."""
        results: list[SignalResult] = []

        # Generar señales recorriendo la historia
        for i in range(252, len(bars)):  # Necesitamos al menos 252 días para SMA200
            # Datos disponibles hasta este punto
            available = bars[: i + 1]
            completed = completed_bars(available, asset_class, now)

            if len(completed) < 51:
                continue

            # Intentar generar señal con los datos disponibles
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

            # Verificar si ya tenemos una señal abierta para este activo
            open_signals = [r for r in results if r.status == "open"]
            if any(r.as_of >= as_of for r in open_signals):
                continue

            # Datos futuros para evaluar la señal
            future_bars = [bar for bar in bars if str(bar["time"]) > as_of]

            # Evaluar la señal
            outcome = evaluate(
                signal["entry"],
                signal["stop"],
                signal["target"],
                future_bars,
                signal["horizon_sessions"],
                commission,
            )

            if outcome is None:
                # La señal queda abierta (no hay suficientes datos futuros)
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

            # Calcular rendimientos de referencia
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
    watchlist: list[dict[str, str]],
    config: BacktestConfig | None = None,
) -> dict[str, Any]:
    """
    Ejecuta el backtest completo para una lista de activos.

    Args:
        watchlist: Lista de activos a analizar
        config: Configuración del backtest (usa defaults si es None)

    Returns:
        Diccionario con resultados completos del backtest
    """
    if config is None:
        config = BacktestConfig()

    # Descargar SPY y BTC para comparación
    spy_bars = _download_historical("SPY", config.lookback_years)
    btc_bars = _download_historical("BTC-USD", config.lookback_years)

    all_in_sample: list[SignalResult] = []
    all_out_of_sample: list[SignalResult] = []

    print(f"Iniciando backtest con {len(watchlist)} activos...")

    for i, item in enumerate(watchlist, 1):
        symbol = item["symbol"]
        yahoo_symbol = item["yahoo_symbol"]
        asset_class = item["asset_class"]

        print(f"[{i}/{len(watchlist)}] Procesando {symbol}...", flush=True)

        in_sample, out_of_sample = backtest_asset(
            symbol, yahoo_symbol, asset_class, config, spy_bars, btc_bars
        )

        all_in_sample.extend(in_sample)
        all_out_of_sample.extend(out_of_sample)

    # Calcular métricas
    in_sample_metrics = _metrics_from_results(all_in_sample)
    out_of_sample_metrics = _metrics_from_results(all_out_of_sample)

    in_sample_by_setup = _metrics_by_setup(all_in_sample)
    out_of_sample_by_setup = _metrics_by_setup(all_out_of_sample)

    return {
        "config": config,
        "in_sample": {
            "signals": all_in_sample,
            "metrics": in_sample_metrics,
            "by_setup": in_sample_by_setup,
        },
        "out_of_sample": {
            "signals": all_out_of_sample,
            "metrics": out_of_sample_metrics,
            "by_setup": out_of_sample_by_setup,
        },
    }
