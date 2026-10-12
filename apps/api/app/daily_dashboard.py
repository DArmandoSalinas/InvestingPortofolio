"""
Dashboard "Qué hacer hoy" - Genera puntos accionables simples.

Analiza el mercado, ranking, señales y perfil del usuario para generar
3-5 recomendaciones concretas en lenguaje simple.
"""

from datetime import date
from typing import Any


def _pct(value: float | None) -> str:
    """Formatea un porcentaje."""
    if value is None:
        return "N/A"
    return f"{value * 100:+.1f}%".replace(".", ",")


def _simple_pct(value: float | None) -> str:
    """Formatea un porcentaje sin signo."""
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%".replace(".", ",")


def analyze_ranking_changes(
    current: list[dict[str, Any]],
    previous: list[dict[str, Any]] | None,
) -> list[str]:
    """
    Analiza cambios en el ranking y genera observaciones.

    Args:
        current: Ranking actual
        previous: Ranking anterior (opcional)

    Returns:
        Lista de observaciones sobre el ranking
    """
    insights: list[str] = []

    # Empresas con alto puntaje general
    top_composite = [r for r in current if r.get("composite", 0) >= 75]
    if top_composite:
        count = len(top_composite)
        top_names = ", ".join(r["name"] for r in top_composite[:3])
        if count <= 3:
            insights.append(
                f"Hay {count} empresa{'s' if count != 1 else ''} con puntaje general alto (≥75): {top_names}."
            )
        else:
            insights.append(
                f"Hay {count} empresas con puntaje general alto (≥75). Las principales: {top_names}."
            )

    # Empresas con calidad alta
    high_quality = [r for r in current if r.get("quality", 0) >= 75]
    if high_quality:
        count = len(high_quality)
        quality_names = ", ".join(r["name"] for r in high_quality[:3])
        if count <= 3:
            insights.append(
                f"{'Esta empresa tiene' if count == 1 else 'Estas empresas tienen'} calidad fundamental alta: {quality_names}."
            )
        else:
            insights.append(
                f"{count} empresas tienen calidad fundamental alta. Destacan: {quality_names}."
            )

    # Altas en los tres estilos
    triple_high = [
        r
        for r in current
        if r.get("growth", 0) >= 70 and r.get("value", 0) >= 70 and r.get("momentum", 0) >= 70
    ]
    if triple_high:
        names = ", ".join(r["name"] for r in triple_high[:2])
        insights.append(
            f"{'Destaca' if len(triple_high) == 1 else 'Destacan'} {names} con puntuación alta en los tres estilos."
        )

    # Si hay ranking previo, detectar grandes cambios
    if previous:
        prev_map = {(r["market"], r["symbol"]): r for r in previous}

        big_movers: list[tuple[dict[str, Any], int]] = []
        for curr in current:
            prev = prev_map.get((curr["market"], curr["symbol"]))
            if prev:
                curr_composite = curr.get("composite") or 0
                prev_composite = prev.get("composite") or 0
                change = curr_composite - prev_composite
                if abs(change) >= 15:
                    big_movers.append((curr, change))

        if big_movers:
            # Tomar los 2 mayores cambios
            big_movers.sort(key=lambda x: abs(x[1]), reverse=True)
            for company, change in big_movers[:2]:
                direction = "subió" if change > 0 else "bajó"
                insights.append(
                    f"{company['name']} {direction} {abs(change)} puntos en el ranking general."
                )

    if not insights:
        insights.append("El ranking está estable. Revisa las empresas con mayor puntaje general.")

    return insights


def analyze_signals(
    signals: list[dict[str, Any]],
    performance: dict[str, dict[str, Any]] | None,
) -> list[str]:
    """
    Analiza señales activas y su contexto.

    Args:
        signals: Lista de señales
        performance: Métricas de desempeño por tipo (opcional)

    Returns:
        Lista de observaciones sobre señales
    """
    insights: list[str] = []

    open_signals = [s for s in signals if s.get("status") == "open"]

    if not open_signals:
        insights.append("No hay señales abiertas en este momento.")
        return insights

    # Agrupar por tipo
    by_setup: dict[str, list[dict[str, Any]]] = {}
    for signal in open_signals:
        setup = signal.get("setup", "")
        if setup not in by_setup:
            by_setup[setup] = []
        by_setup[setup].append(signal)

    # Resumen de señales abiertas
    count = len(open_signals)
    if count == 1:
        signal = open_signals[0]
        setup_name = "impulso" if signal.get("setup") == "impulso" else "retroceso"
        insights.append(
            f"Hay una señal abierta ({setup_name}) en {signal['name']}: "
            f"entrada {signal.get('entry', 0):.2f}, objetivo {signal.get('target', 0):.2f}."
        )
    else:
        setup_counts = ", ".join(
            f"{len(sigs)} de {setup}" for setup, sigs in by_setup.items()
        )
        insights.append(f"Hay {count} señales abiertas: {setup_counts}.")

    # Agregar contexto de desempeño histórico
    if performance:
        for setup, perf in performance.items():
            if setup in by_setup and perf.get("hit_rate") is not None:
                hit_rate = perf["hit_rate"]
                insights.append(
                    f"Las señales de {setup} han alcanzado el objetivo en {_simple_pct(hit_rate)} de los casos históricos."
                )

    return insights


def analyze_market_context(spy_data: dict[str, Any] | None, btc_data: dict[str, Any] | None) -> list[str]:
    """
    Analiza el contexto del mercado general.

    Args:
        spy_data: Datos de SPY (cambio reciente)
        btc_data: Datos de BTC (cambio reciente)

    Returns:
        Lista de observaciones sobre el mercado
    """
    insights: list[str] = []

    if spy_data and spy_data.get("return") is not None:
        spy_return = spy_data["return"]
        period = spy_data.get("period", "reciente")
        if abs(spy_return) >= 0.02:
            direction = "subió" if spy_return > 0 else "bajó"
            insights.append(f"El S&P 500 {direction} {_pct(spy_return)} {period}.")

    if btc_data and btc_data.get("return") is not None:
        btc_return = btc_data["return"]
        period = btc_data.get("period", "reciente")
        if abs(btc_return) >= 0.05:
            direction = "subió" if btc_return > 0 else "bajó"
            insights.append(f"Bitcoin {direction} {_pct(btc_return)} {period}.")

    if not insights:
        insights.append("Los mercados principales se mantienen sin grandes movimientos.")

    return insights


def suggest_actions(
    profile: dict[str, Any] | None,
    ranking: list[dict[str, Any]],
    signals: list[dict[str, Any]],
) -> list[str]:
    """
    Genera sugerencias de acción basadas en el perfil del usuario.

    Args:
        profile: Perfil del inversionista (opcional)
        ranking: Ranking actual
        signals: Señales actuales

    Returns:
        Lista de acciones sugeridas
    """
    actions: list[str] = []

    # Si hay perfil, considerar el estilo de riesgo
    if profile:
        risk = profile.get("risk", "")
        horizon = profile.get("horizon_years", 0)

        if risk == "bajo":
            # Recomendar empresas de calidad
            quality_companies = [r for r in ranking if r.get("quality", 0) >= 75]
            if quality_companies:
                top = quality_companies[0]
                actions.append(
                    f"Con tu perfil conservador, revisa {top['name']} (calidad {top.get('quality')})."
                )

        elif risk == "alto" and horizon >= 5:
            # Recomendar empresas de crecimiento
            growth_companies = [r for r in ranking if r.get("growth", 0) >= 75]
            if growth_companies:
                top = growth_companies[0]
                actions.append(
                    f"Para tu perfil de riesgo alto y plazo largo, considera {top['name']} (crecimiento {top.get('growth')})."
                )

    # Sugerencia genérica: revisar el top 3
    if len(ranking) >= 3:
        top_3 = ranking[:3]
        names = ", ".join(r["name"] for r in top_3)
        actions.append(f"Revisa con detalle el top 3 del ranking: {names}.")

    # Si hay señales, recordar monitorearlas
    open_signals = [s for s in signals if s.get("status") == "open"]
    if open_signals:
        actions.append(
            f"Monitorea {'la señal abierta' if len(open_signals) == 1 else f'las {len(open_signals)} señales abiertas'} en el Historial."
        )

    if not actions:
        actions.append("Explora el ranking completo para encontrar oportunidades.")

    return actions


def generate_daily_dashboard(
    ranking_current: list[dict[str, Any]],
    ranking_previous: list[dict[str, Any]] | None,
    signals: list[dict[str, Any]],
    performance: dict[str, dict[str, Any]] | None,
    spy_data: dict[str, Any] | None = None,
    btc_data: dict[str, Any] | None = None,
    profile: dict[str, Any] | None = None,
    as_of: date | None = None,
) -> dict[str, Any]:
    """
    Genera el dashboard completo "qué hacer hoy".

    Args:
        ranking_current: Ranking actual
        ranking_previous: Ranking anterior (opcional)
        signals: Lista de todas las señales
        performance: Métricas de desempeño por tipo
        spy_data: Datos de SPY (opcional)
        btc_data: Datos de BTC (opcional)
        profile: Perfil del inversionista (opcional)
        as_of: Fecha del dashboard (opcional)

    Returns:
        Diccionario con el dashboard completo
    """
    # Recopilar todos los insights
    all_insights: list[str] = []

    # 1. Contexto del mercado
    market_insights = analyze_market_context(spy_data, btc_data)
    all_insights.extend(market_insights)

    # 2. Cambios en el ranking
    ranking_insights = analyze_ranking_changes(ranking_current, ranking_previous)
    all_insights.extend(ranking_insights)

    # 3. Señales activas
    signal_insights = analyze_signals(signals, performance)
    all_insights.extend(signal_insights)

    # 4. Acciones sugeridas
    action_insights = suggest_actions(profile, ranking_current, signals)
    all_insights.extend(action_insights)

    # Limitar a 5 puntos más relevantes
    # Priorizar: 1 mercado, 2 ranking, 1 señal, 1 acción
    selected: list[str] = []

    if market_insights:
        selected.append(market_insights[0])

    if ranking_insights:
        selected.extend(ranking_insights[:2])

    if signal_insights and len(selected) < 4:
        selected.append(signal_insights[0])

    if action_insights and len(selected) < 5:
        selected.append(action_insights[0])

    # Si todavía no llegamos a 3, agregar más de donde haya
    remaining = 5 - len(selected)
    if remaining > 0:
        for insight in all_insights:
            if insight not in selected:
                selected.append(insight)
                if len(selected) >= 5:
                    break

    # Asegurar al menos 3 puntos
    if len(selected) < 3:
        selected.extend(all_insights[: 3 - len(selected)])

    return {
        "as_of": as_of.isoformat() if as_of else None,
        "insights": selected[:5],  # Máximo 5 puntos
        "market_summary": market_insights[0] if market_insights else None,
        "has_open_signals": any(s.get("status") == "open" for s in signals),
        "top_company": ranking_current[0] if ranking_current else None,
    }
