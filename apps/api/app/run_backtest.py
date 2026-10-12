"""
Script para ejecutar el backtest con el universo completo de la base de datos.

Usa caché de descargas para optimizar tiempo.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from app.backtest import BacktestConfig, BacktestMetrics, SetupMetrics, run_backtest
from app.load_backtest_performance import SUMMARY_PATH, compact_summary_from_results


def get_universe_fallback() -> list[dict[str, str]]:
    """Universo de prueba (top S&P 500 + IPC + crypto)."""
    return [
        # Tech
        {"symbol": "AAPL", "yahoo_symbol": "AAPL", "asset_class": "stock"},
        {"symbol": "MSFT", "yahoo_symbol": "MSFT", "asset_class": "stock"},
        {"symbol": "NVDA", "yahoo_symbol": "NVDA", "asset_class": "stock"},
        {"symbol": "AMZN", "yahoo_symbol": "AMZN", "asset_class": "stock"},
        {"symbol": "META", "yahoo_symbol": "META", "asset_class": "stock"},
        {"symbol": "GOOGL", "yahoo_symbol": "GOOGL", "asset_class": "stock"},
        {"symbol": "TSLA", "yahoo_symbol": "TSLA", "asset_class": "stock"},
        {"symbol": "AMD", "yahoo_symbol": "AMD", "asset_class": "stock"},
        {"symbol": "NFLX", "yahoo_symbol": "NFLX", "asset_class": "stock"},
        {"symbol": "AVGO", "yahoo_symbol": "AVGO", "asset_class": "stock"},
        # Finance
        {"symbol": "JPM", "yahoo_symbol": "JPM", "asset_class": "stock"},
        {"symbol": "BAC", "yahoo_symbol": "BAC", "asset_class": "stock"},
        {"symbol": "WFC", "yahoo_symbol": "WFC", "asset_class": "stock"},
        {"symbol": "V", "yahoo_symbol": "V", "asset_class": "stock"},
        {"symbol": "MA", "yahoo_symbol": "MA", "asset_class": "stock"},
        # Consumer
        {"symbol": "WMT", "yahoo_symbol": "WMT", "asset_class": "stock"},
        {"symbol": "COST", "yahoo_symbol": "COST", "asset_class": "stock"},
        {"symbol": "HD", "yahoo_symbol": "HD", "asset_class": "stock"},
        {"symbol": "MCD", "yahoo_symbol": "MCD", "asset_class": "stock"},
        {"symbol": "NKE", "yahoo_symbol": "NKE", "asset_class": "stock"},
        # Healthcare
        {"symbol": "JNJ", "yahoo_symbol": "JNJ", "asset_class": "stock"},
        {"symbol": "UNH", "yahoo_symbol": "UNH", "asset_class": "stock"},
        {"symbol": "LLY", "yahoo_symbol": "LLY", "asset_class": "stock"},
        {"symbol": "PFE", "yahoo_symbol": "PFE", "asset_class": "stock"},
        {"symbol": "ABBV", "yahoo_symbol": "ABBV", "asset_class": "stock"},
        # Energy
        {"symbol": "XOM", "yahoo_symbol": "XOM", "asset_class": "stock"},
        {"symbol": "CVX", "yahoo_symbol": "CVX", "asset_class": "stock"},
        {"symbol": "COP", "yahoo_symbol": "COP", "asset_class": "stock"},
        # Industrials
        {"symbol": "BA", "yahoo_symbol": "BA", "asset_class": "stock"},
        {"symbol": "CAT", "yahoo_symbol": "CAT", "asset_class": "stock"},
        {"symbol": "GE", "yahoo_symbol": "GE", "asset_class": "stock"},
        # Telecom/Media
        {"symbol": "DIS", "yahoo_symbol": "DIS", "asset_class": "stock"},
        {"symbol": "CMCSA", "yahoo_symbol": "CMCSA", "asset_class": "stock"},
        {"symbol": "T", "yahoo_symbol": "T", "asset_class": "stock"},
        # IPC (México)
        {"symbol": "WALMEX", "yahoo_symbol": "WALMEX.MX", "asset_class": "stock"},
        {"symbol": "FEMSA", "yahoo_symbol": "FEMSAUBD.MX", "asset_class": "stock"},
        {"symbol": "GMEXICO", "yahoo_symbol": "GMEXICOB.MX", "asset_class": "stock"},
        {"symbol": "CEMEX", "yahoo_symbol": "CEMEXCPO.MX", "asset_class": "stock"},
        {"symbol": "AMXL", "yahoo_symbol": "AMXL.MX", "asset_class": "stock"},
        # Crypto
        {"symbol": "BTC", "yahoo_symbol": "BTC-USD", "asset_class": "crypto"},
        {"symbol": "ETH", "yahoo_symbol": "ETH-USD", "asset_class": "crypto"},
    ]


def format_metrics_section(title: str, metrics: BacktestMetrics) -> str:
    """Formatea una sección de métricas para el reporte."""
    def fmt_pct(value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value * 100:.2f}%"
    
    def fmt_num(value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value * 100:+.2f}%"
    
    lines = [
        f"### {title}",
        "",
        f"- **Total de señales:** {metrics.total_signals}",
        f"- **Tasa de acierto (target):** {fmt_pct(metrics.target_hit_rate)}",
        f"- **Tasa de retornos positivos:** {fmt_pct(metrics.positive_return_rate)}",
        f"- **Tasa que supera SPY:** {fmt_pct(metrics.beats_spy_rate)}",
        f"- **Rendimiento neto promedio:** {fmt_num(metrics.avg_net_return)}",
        f"- **SPY promedio (misma ventana):** {fmt_num(metrics.avg_spy_return)}",
        f"- **BTC promedio (misma ventana):** {fmt_num(metrics.avg_btc_return)}",
        f"- **Pérdida máxima por operación:** {fmt_num(metrics.max_loss_per_trade)}",
        f"- **Drawdown de portafolio (10% posición, máx 10):** {fmt_num(metrics.portfolio_max_drawdown)}",
        f"- **Objetivos alcanzados:** {metrics.targets}",
        f"- **Stops activados:** {metrics.stops}",
        f"- **Expiradas:** {metrics.expired}",
        f"- **Ganancia promedio (ganadoras):** {fmt_num(metrics.avg_winner)}",
        f"- **Pérdida promedio (perdedoras):** {fmt_num(metrics.avg_loser)}",
        f"- **Ratio ganancia/pérdida:** {f'{metrics.win_loss_ratio:.2f}' if metrics.win_loss_ratio else 'N/A'}",
        "",
    ]
    return "\n".join(lines)


def format_setup_section(title: str, by_setup: dict[str, SetupMetrics]) -> str:
    """Formatea métricas por tipo de setup."""
    def fmt_pct(value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value * 100:.2f}%"
    
    def fmt_num(value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value * 100:+.2f}%"
    
    lines = [f"### {title}", ""]
    
    for setup_name in sorted(by_setup.keys()):
        metrics = by_setup[setup_name]
        lines.extend([
            f"#### {setup_name.capitalize()}",
            "",
            f"- **Señales:** {metrics.total}",
            f"- **Tasa de acierto (target):** {fmt_pct(metrics.target_hit_rate)}",
            f"- **Tasa de retornos positivos:** {fmt_pct(metrics.positive_return_rate)}",
            f"- **Tasa que supera SPY:** {fmt_pct(metrics.beats_spy_rate)}",
            f"- **Rendimiento neto promedio:** {fmt_num(metrics.avg_net_return)}",
            f"- **Objetivos:** {metrics.targets} | **Stops:** {metrics.stops} | **Expiradas:** {metrics.expired}",
            "",
        ])
    
    return "\n".join(lines)


def generate_report(results: dict[str, any], config: BacktestConfig) -> str:
    """Genera reporte markdown de resultados."""
    in_metrics: BacktestMetrics = results["in_sample"]["metrics"]
    out_metrics: BacktestMetrics = results["out_of_sample"]["metrics"]
    in_by_setup: dict[str, SetupMetrics] = results["in_sample"]["by_setup"]
    out_by_setup: dict[str, SetupMetrics] = results["out_of_sample"]["by_setup"]
    
    lines = [
        "# Resultados del Backtest de Señales (Corregido)",
        "",
        f"**Fecha de ejecución:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "## Configuración",
        "",
        f"- **Años de historia:** {config.lookback_years}",
        f"- **Comisión acciones:** {config.stock_commission * 100:.2f}%",
        f"- **Comisión crypto:** {config.crypto_commission * 100:.2f}%",
        f"- **Horizonte:** {config.horizon_sessions} sesiones",
        f"- **División de datos:** {int(config.in_sample_ratio * 100)}% in-sample, {int((1 - config.in_sample_ratio) * 100)}% out-of-sample",
        f"- **Simulación de portafolio:** {config.position_size * 100:.0f}% por posición, máximo {config.max_positions} posiciones",
        "",
        "## Definiciones de Métricas",
        "",
        "- **Tasa de acierto (target):** Porcentaje de señales que alcanzaron el precio objetivo (no stop ni expiró)",
        "- **Tasa de retornos positivos:** Porcentaje de señales con rendimiento neto > 0 (incluye expiradas positivas)",
        "- **Tasa que supera SPY:** Porcentaje de señales con mejor rendimiento que SPY en la misma ventana temporal",
        "- **Pérdida máxima por operación:** La peor pérdida individual registrada",
        "- **Drawdown de portafolio:** Simulado con posición fija del 10% y máximo 10 posiciones simultáneas",
        "",
        "## Resumen Ejecutivo",
        "",
    ]
    
    lines.append(format_metrics_section("In-Sample (Entrenamiento)", in_metrics))
    lines.append(format_metrics_section("Out-of-Sample (Validación)", out_metrics))
    
    lines.extend([
        "## Desempeño por Tipo de Señal",
        "",
    ])
    
    lines.append(format_setup_section("In-Sample", in_by_setup))
    lines.append(format_setup_section("Out-of-Sample", out_by_setup))
    
    lines.extend([
        "## Interpretación y Conclusiones",
        "",
        "### Validez del Modelo",
        "",
        "El modelo es válido si:",
        "",
        "1. **Consistencia:** Las métricas out-of-sample son similares a las in-sample",
        "2. **Superioridad vs SPY:** La tasa que supera SPY es > 50% en out-of-sample",
        "3. **Retornos positivos:** El rendimiento neto promedio es positivo y supera a SPY",
        "",
        "### Recomendaciones",
        "",
    ])
    
    # Evaluar automáticamente
    if out_metrics.beats_spy_rate and out_metrics.beats_spy_rate <= 0.5:
        lines.append("⚠️ **ALERTA:** La tasa que supera SPY es ≤ 50% en out-of-sample. El sistema NO agrega valor sobre buy-and-hold.")
        lines.append("")
    
    if out_metrics.avg_net_return and out_metrics.avg_spy_return:
        if out_metrics.avg_net_return < out_metrics.avg_spy_return:
            lines.append("⚠️ **REVISAR:** El rendimiento promedio es inferior a SPY en out-of-sample.")
            lines.append("")
    
    # Evaluar por setup
    lines.extend([
        "### Por Tipo de Señal",
        "",
    ])
    
    for setup_name, setup_metrics in out_by_setup.items():
        if setup_metrics.beats_spy_rate and setup_metrics.beats_spy_rate > 0.5:
            lines.append(f"✓ **{setup_name.capitalize()}:** Supera a SPY en {setup_metrics.beats_spy_rate * 100:.1f}% de los casos (>50%). VÁLIDO.")
        else:
            rate = setup_metrics.beats_spy_rate * 100 if setup_metrics.beats_spy_rate else 0
            lines.append(f"❌ **{setup_name.capitalize()}:** Solo supera a SPY en {rate:.1f}% de los casos (≤50%). DESACTIVAR.")
        lines.append("")
    
    lines.extend([
        "## Limitaciones",
        "",
        "1. **Slippage:** No se modela el deslizamiento de precio en la ejecución",
        "2. **Liquidez:** Asume que siempre se puede entrar/salir al precio deseado",
        "3. **Costos de oportunidad:** No considera el costo de tener capital inmovilizado",
        "4. **Survivorship bias:** Solo incluye activos que existen actualmente",
        "",
        "## Notas Metodológicas",
        "",
        "- Las señales se generan usando solo información disponible hasta ese momento (sin look-ahead)",
        "- La entrada es al día siguiente del cierre que generó la señal",
        "- Si stop y objetivo se tocan el mismo día, se registra el stop (conservador)",
        "- Las comisiones se descuentan del rendimiento bruto",
        "- Los rendimientos de SPY/BTC se calculan para el mismo periodo de cada señal",
        "- El drawdown de portafolio simula posiciones del 10% con máximo 10 simultáneas",
        "- Precios ajustados por splits y dividendos (yfinance)",
    ])
    
    return "\n".join(lines)


def main():
    """Ejecuta el backtest completo."""
    print("=" * 80)
    print("BACKTEST DE SEÑALES (CORREGIDO)")
    print("=" * 80)
    print()
    
    # Usar universo de prueba
    print("Usando universo de prueba (41 activos representativos)...")
    universe = get_universe_fallback()
    print(f"Universo: {len(universe)} activos")
    print()
    
    # Configuración
    config = BacktestConfig(
        stock_commission=0.001,
        crypto_commission=0.002,
        horizon_sessions=10,
        lookback_years=5,
        in_sample_ratio=0.6,
        position_size=0.10,
        max_positions=10,
    )
    
    # Ejecutar backtest
    print("Ejecutando backtest...")
    print(f"Activos a analizar: {len(universe)}")
    print()
    
    results = run_backtest(universe, config)
    
    # Generar reportes
    print()
    print("=" * 80)
    print("GENERANDO REPORTES")
    print("=" * 80)
    print()
    
    report = generate_report(results, config)
    
    with open("BACKTEST_RESULTS.md", "w") as f:
        f.write(report)
    print("Reporte guardado en: BACKTEST_RESULTS.md")
    
    summary = compact_summary_from_results(results)
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Resumen compacto por regla guardado en: {SUMMARY_PATH}")
    
    print()
    print("=" * 80)
    print("BACKTEST COMPLETADO")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
