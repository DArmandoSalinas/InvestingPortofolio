"""
Script para ejecutar el backtest y generar reporte.

Uso:
    python -m app.run_backtest
"""

import json
from datetime import datetime

from app.backtest import BacktestConfig, run_backtest
from app.signals import WATCHLIST


def _format_pct(value: float | None) -> str:
    """Formatea un valor como porcentaje."""
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%".replace(".", ",")


def _format_ratio(value: float | None) -> str:
    """Formatea un ratio."""
    if value is None:
        return "N/A"
    return f"{value:.2f}".replace(".", ",")


def generate_report(results: dict) -> str:
    """
    Genera un reporte en markdown del backtest.

    Args:
        results: Resultados del backtest

    Returns:
        Reporte en formato markdown
    """
    config = results["config"]
    in_sample = results["in_sample"]
    out_of_sample = results["out_of_sample"]

    in_metrics = in_sample["metrics"]
    out_metrics = out_of_sample["metrics"]

    in_by_setup = in_sample["by_setup"]
    out_by_setup = out_of_sample["by_setup"]

    report_lines = [
        "# Resultados del Backtest de Señales",
        "",
        f"**Fecha de ejecución:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Configuración",
        "",
        f"- **Años de historia:** {config.lookback_years}",
        f"- **Comisión acciones:** {_format_pct(config.stock_commission)}",
        f"- **Comisión crypto:** {_format_pct(config.crypto_commission)}",
        f"- **Horizonte:** {config.horizon_sessions} sesiones",
        f"- **División de datos:** {int(config.in_sample_ratio * 100)}% in-sample, {int((1 - config.in_sample_ratio) * 100)}% out-of-sample",
        "",
        "## Resumen Ejecutivo",
        "",
        "### In-Sample (Entrenamiento)",
        "",
        f"- **Total de señales:** {in_metrics.total_signals}",
        f"- **Tasa de acierto:** {_format_pct(in_metrics.hit_rate)}",
        f"- **Rendimiento neto promedio:** {_format_pct(in_metrics.avg_net_return)}",
        f"- **SPY promedio (mismo periodo):** {_format_pct(in_metrics.avg_spy_return)}",
        f"- **BTC promedio (mismo periodo):** {_format_pct(in_metrics.avg_btc_return)}",
        f"- **Drawdown máximo:** {_format_pct(in_metrics.max_drawdown)}",
        f"- **Objetivos alcanzados:** {in_metrics.targets}",
        f"- **Stops activados:** {in_metrics.stops}",
        f"- **Expiradas:** {in_metrics.expired}",
        f"- **Ganancia promedio (ganadoras):** {_format_pct(in_metrics.avg_winner)}",
        f"- **Pérdida promedio (perdedoras):** {_format_pct(in_metrics.avg_loser)}",
        f"- **Ratio ganancia/pérdida:** {_format_ratio(in_metrics.win_loss_ratio)}",
        "",
        "### Out-of-Sample (Validación)",
        "",
        f"- **Total de señales:** {out_metrics.total_signals}",
        f"- **Tasa de acierto:** {_format_pct(out_metrics.hit_rate)}",
        f"- **Rendimiento neto promedio:** {_format_pct(out_metrics.avg_net_return)}",
        f"- **SPY promedio (mismo periodo):** {_format_pct(out_metrics.avg_spy_return)}",
        f"- **BTC promedio (mismo periodo):** {_format_pct(out_metrics.avg_btc_return)}",
        f"- **Drawdown máximo:** {_format_pct(out_metrics.max_drawdown)}",
        f"- **Objetivos alcanzados:** {out_metrics.targets}",
        f"- **Stops activados:** {out_metrics.stops}",
        f"- **Expiradas:** {out_metrics.expired}",
        f"- **Ganancia promedio (ganadoras):** {_format_pct(out_metrics.avg_winner)}",
        f"- **Pérdida promedio (perdedoras):** {_format_pct(out_metrics.avg_loser)}",
        f"- **Ratio ganancia/pérdida:** {_format_ratio(out_metrics.win_loss_ratio)}",
        "",
        "## Desempeño por Tipo de Señal",
        "",
        "### In-Sample",
        "",
    ]

    for setup, metrics in in_by_setup.items():
        report_lines.extend(
            [
                f"#### {setup.capitalize()}",
                "",
                f"- **Señales:** {metrics.total}",
                f"- **Tasa de acierto:** {_format_pct(metrics.hit_rate)}",
                f"- **Rendimiento neto promedio:** {_format_pct(metrics.avg_net_return)}",
                f"- **Objetivos:** {metrics.targets} | Stops: {metrics.stops} | Expiradas: {metrics.expired}",
                "",
            ]
        )

    report_lines.extend(
        [
            "### Out-of-Sample",
            "",
        ]
    )

    for setup, metrics in out_by_setup.items():
        report_lines.extend(
            [
                f"#### {setup.capitalize()}",
                "",
                f"- **Señales:** {metrics.total}",
                f"- **Tasa de acierto:** {_format_pct(metrics.hit_rate)}",
                f"- **Rendimiento neto promedio:** {_format_pct(metrics.avg_net_return)}",
                f"- **Objetivos:** {metrics.targets} | Stops: {metrics.stops} | Expiradas: {metrics.expired}",
                "",
            ]
        )

    report_lines.extend(
        [
            "## Interpretación y Conclusiones",
            "",
            "### Validez del Modelo",
            "",
            "El modelo es válido si:",
            "",
            "1. **Consistencia:** Las métricas out-of-sample son similares a las in-sample",
            "   - Si out-of-sample es mucho peor, hay sobreajuste",
            "   - Si out-of-sample es mucho mejor, puede ser suerte (revisar con más datos)",
            "",
            "2. **Superioridad:** El rendimiento neto supera a comprar y mantener SPY/BTC",
            "   - Ajustado por el riesgo (considerar drawdown)",
            "",
            "3. **Ratio ganancia/pérdida:** Debe ser > 1.0 para compensar tasa de acierto < 100%",
            "",
            "### Recomendaciones",
            "",
        ]
    )

    # Análisis automático
    if out_metrics.avg_net_return is not None and in_metrics.avg_net_return is not None:
        degradation = (
            abs(out_metrics.avg_net_return - in_metrics.avg_net_return)
            / abs(in_metrics.avg_net_return)
            if in_metrics.avg_net_return != 0
            else 0
        )

        if degradation > 0.5:
            report_lines.append(
                "⚠️ **ALERTA:** Degradación significativa en out-of-sample (>50%). "
                "Posible sobreajuste. Revisar reglas."
            )
        elif degradation > 0.3:
            report_lines.append(
                "⚠️ **PRECAUCIÓN:** Degradación moderada en out-of-sample (>30%). "
                "Monitorear de cerca."
            )
        else:
            report_lines.append(
                "✓ **BUENO:** Degradación aceptable en out-of-sample (<30%). "
                "El modelo generaliza bien."
            )

    report_lines.append("")

    if (
        out_metrics.avg_net_return is not None
        and out_metrics.avg_spy_return is not None
        and out_metrics.avg_net_return > out_metrics.avg_spy_return
    ):
        excess = out_metrics.avg_net_return - out_metrics.avg_spy_return
        report_lines.append(
            f"✓ **BUENO:** Superioridad sobre SPY de {_format_pct(excess)} en promedio."
        )
    else:
        report_lines.append(
            "⚠️ **REVISAR:** No supera consistentemente a comprar y mantener SPY."
        )

    report_lines.append("")

    if out_metrics.win_loss_ratio is not None:
        if out_metrics.win_loss_ratio > 1.5:
            report_lines.append(
                f"✓ **EXCELENTE:** Ratio ganancia/pérdida de {_format_ratio(out_metrics.win_loss_ratio)} "
                "es muy favorable."
            )
        elif out_metrics.win_loss_ratio > 1.0:
            report_lines.append(
                f"✓ **BUENO:** Ratio ganancia/pérdida de {_format_ratio(out_metrics.win_loss_ratio)} "
                "es positivo."
            )
        else:
            report_lines.append(
                f"⚠️ **REVISAR:** Ratio ganancia/pérdida de {_format_ratio(out_metrics.win_loss_ratio)} "
                "es bajo. Las pérdidas promedio son mayores que las ganancias."
            )

    report_lines.extend(
        [
            "",
            "## Limitaciones",
            "",
            "1. **Slippage:** No se modela el deslizamiento de precio en la ejecución",
            "2. **Liquidez:** Asume que siempre se puede entrar/salir al precio deseado",
            "3. **Costos de oportunidad:** No considera el costo de tener capital inmovilizado",
            "4. **Survivorship bias:** Solo incluye activos que existen actualmente",
            "5. **Datos históricos:** Usa precios ajustados que pueden no reflejar la realidad del momento",
            "",
            "## Notas Metodológicas",
            "",
            "- Las señales se generan usando solo información disponible hasta ese momento",
            "- Si stop y objetivo se tocan el mismo día, se registra el stop (asunción conservadora)",
            "- Las comisiones se descuentan del rendimiento bruto",
            "- Los rendimientos de SPY/BTC se calculan para el mismo periodo de cada señal",
            "- El drawdown se calcula sobre la curva de capital acumulada",
            "",
        ]
    )

    return "\n".join(report_lines)


def save_detailed_results(results: dict, filename: str = "backtest_results.json") -> None:
    """
    Guarda los resultados detallados en JSON.

    Args:
        results: Resultados del backtest
        filename: Nombre del archivo de salida
    """

    def _serialize(obj):
        """Serializa objetos especiales."""
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=_serialize)

    print(f"\nResultados detallados guardados en: {filename}")


def main():
    """Ejecuta el backtest y genera reportes."""
    print("=" * 80)
    print("BACKTEST DE SEÑALES")
    print("=" * 80)
    print()

    config = BacktestConfig(
        lookback_years=5,
        in_sample_ratio=0.6,
    )

    print("Ejecutando backtest...")
    print(f"Activos a analizar: {len(WATCHLIST)}")
    print()

    results = run_backtest(WATCHLIST, config)

    print()
    print("=" * 80)
    print("GENERANDO REPORTES")
    print("=" * 80)
    print()

    # Generar reporte markdown
    report = generate_report(results)

    report_filename = "BACKTEST_RESULTS.md"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Reporte guardado en: {report_filename}")

    # Guardar resultados detallados
    save_detailed_results(results)

    print()
    print("=" * 80)
    print("BACKTEST COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    main()
