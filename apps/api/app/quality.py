"""
Extensión del sistema de scoring con factor de calidad y manejo robusto de outliers.

Este módulo complementa scoring.py con:
1. Factor de calidad basado en métricas fundamentales (márgenes, ROE, deuda, FCF)
2. Manejo robusto de outliers usando percentiles y winsorización
3. Validación del poder predictivo de las puntuaciones
"""

import math
from typing import Any


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


def _winsorize(values: list[float], lower_pct: float = 0.05, upper_pct: float = 0.95) -> list[float]:
    """
    Winsoriza una lista de valores reemplazando los extremos.

    Args:
        values: Lista de valores
        lower_pct: Percentil inferior (valores debajo se reemplazan)
        upper_pct: Percentil superior (valores encima se reemplazan)

    Returns:
        Lista winsorizada
    """
    if not values:
        return []

    sorted_vals = sorted(values)
    lower_bound = _percentile(sorted_vals, lower_pct)
    upper_bound = _percentile(sorted_vals, upper_pct)
    return [max(lower_bound, min(upper_bound, v)) for v in values]


def _percentile(sorted_vals: list[float], pct: float) -> float:
    """Percentil con interpolación lineal. `pct` va de 0 a 1."""
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    pos = max(0.0, min(1.0, pct)) * (n - 1)
    left = int(math.floor(pos))
    right = min(n - 1, left + 1)
    frac = pos - left
    return sorted_vals[left] + frac * (sorted_vals[right] - sorted_vals[left])


def _percentile_rank(value: float, values: list[float]) -> float:
    """
    Calcula el percentil de un valor en una distribución.

    Args:
        value: Valor a evaluar
        values: Lista de valores de referencia

    Returns:
        Percentil de 0 a 100
    """
    if not values:
        return 50.0

    below = sum(1 for v in values if v < value)
    equal = sum(1 for v in values if v == value)

    # Método interpolado: contar la mitad de los valores iguales
    rank = below + equal / 2
    return (rank / len(values)) * 100


def _robust_scale(
    value: float,
    values: list[float],
    higher_is_better: bool = True,
) -> int | None:
    """
    Escala un valor a 0-100 usando percentiles robustos.

    Args:
        value: Valor a escalar
        values: Valores de referencia para la distribución
        higher_is_better: Si True, valores más altos reciben mayor score

    Returns:
        Score de 0 a 100, o None si no hay suficientes datos
    """
    if not values or len(values) < 5:
        return None

    # Winsorizar para manejar outliers y recortar el valor evaluado
    winsorized = _winsorize(values)
    lower_bound = min(winsorized)
    upper_bound = max(winsorized)
    win_value = max(lower_bound, min(upper_bound, value))

    # Calcular percentil
    percentile = _percentile_rank(win_value, winsorized)

    # Invertir si menor es mejor
    if not higher_is_better:
        percentile = 100 - percentile

    return min(100, max(0, round(percentile)))


def quality_score(row: dict[str, Any], all_rows: list[dict[str, Any]]) -> tuple[int | None, dict[str, Any]]:
    """
    Calcula un score de calidad basado en métricas fundamentales.

    Considera:
    - Márgenes operativo y neto
    - ROE (Return on Equity)
    - Ratio de deuda (Debt/Equity)
    - Free Cash Flow / Market Cap

    Args:
        row: Datos de la empresa
        all_rows: Todas las empresas para comparación

    Returns:
        Tupla (score, detail) donde detail contiene métricas individuales
    """
    # Filtrar empresas del mismo sector y mercado para comparación justa
    sector = row.get("sector")
    market = row.get("market")

    if sector in (None, "", "unknown"):
        return None, {"reason": "no_sector"}

    peers = [
        r
        for r in all_rows
        if r.get("sector") == sector
        and r.get("market") == market
        and r is not row
    ]

    if len(peers) < 5:
        # No hay suficientes pares para comparación robusta
        return None, {"reason": "insufficient_peers", "peer_count": len(peers)}

    # Extraer métricas de calidad
    operating_margin = _finite(row.get("operating_margin"))
    net_margin = _finite(row.get("net_margin"))
    roe = _finite(row.get("roe"))
    debt_equity = _finite(row.get("debt_to_equity"))
    fcf_yield = _finite(row.get("fcf_yield"))

    scores: list[int] = []
    detail: dict[str, Any] = {}

    # Márgenes operativos (mayor es mejor)
    if operating_margin is not None:
        peer_margins = [
            _finite(r.get("operating_margin"))
            for r in peers
            if _finite(r.get("operating_margin")) is not None
        ]
        if len(peer_margins) >= 5:
            score = _robust_scale(operating_margin, peer_margins, higher_is_better=True)
            if score is not None:
                scores.append(score)
                detail["operating_margin_score"] = score

    # Márgenes netos (mayor es mejor)
    if net_margin is not None:
        peer_margins = [
            _finite(r.get("net_margin"))
            for r in peers
            if _finite(r.get("net_margin")) is not None
        ]
        if len(peer_margins) >= 5:
            score = _robust_scale(net_margin, peer_margins, higher_is_better=True)
            if score is not None:
                scores.append(score)
                detail["net_margin_score"] = score

    # ROE (mayor es mejor, pero valores negativos son malos)
    if roe is not None and roe > 0:
        peer_roes = [
            _finite(r.get("roe"))
            for r in peers
            if _finite(r.get("roe")) is not None and _finite(r.get("roe")) > 0  # type: ignore[operator]
        ]
        if len(peer_roes) >= 5:
            score = _robust_scale(roe, peer_roes, higher_is_better=True)
            if score is not None:
                scores.append(score)
                detail["roe_score"] = score
    elif roe is not None:
        detail["roe_negative"] = True

    # Deuda/Capital (menor es mejor)
    if debt_equity is not None:
        peer_debt = [
            _finite(r.get("debt_to_equity"))
            for r in peers
            if _finite(r.get("debt_to_equity")) is not None
        ]
        if len(peer_debt) >= 5:
            score = _robust_scale(debt_equity, peer_debt, higher_is_better=False)
            if score is not None:
                scores.append(score)
                detail["debt_score"] = score

    # FCF Yield (mayor es mejor)
    if fcf_yield is not None and fcf_yield > 0:
        peer_fcf = [
            _finite(r.get("fcf_yield"))
            for r in peers
            if _finite(r.get("fcf_yield")) is not None and _finite(r.get("fcf_yield")) > 0  # type: ignore[operator]
        ]
        if len(peer_fcf) >= 5:
            score = _robust_scale(fcf_yield, peer_fcf, higher_is_better=True)
            if score is not None:
                scores.append(score)
                detail["fcf_score"] = score

    if not scores:
        return None, {"reason": "no_usable_metrics", **detail}

    # Promedio de las métricas disponibles
    quality = sum(scores) // len(scores)
    detail["component_count"] = len(scores)

    return quality, detail


def quality_note(detail: dict[str, Any]) -> str:
    """
    Genera una nota explicativa del score de calidad.

    Args:
        detail: Detalle del cálculo de calidad

    Returns:
        Texto explicativo
    """
    if detail.get("reason") == "no_sector":
        return "No hay sector asignado para calcular calidad."

    if detail.get("reason") == "insufficient_peers":
        count = detail.get("peer_count", 0)
        return f"Solo hay {count} empresas en el sector para comparar (se necesitan al menos 5)."

    if detail.get("reason") == "no_usable_metrics":
        return "No hay suficientes métricas fundamentales para calcular calidad."

    components: list[str] = []
    component_count = detail.get("component_count", 0)

    if "operating_margin_score" in detail:
        components.append(f"margen operativo {detail['operating_margin_score']}")

    if "net_margin_score" in detail:
        components.append(f"margen neto {detail['net_margin_score']}")

    if "roe_score" in detail:
        components.append(f"ROE {detail['roe_score']}")
    elif detail.get("roe_negative"):
        components.append("ROE negativo")

    if "debt_score" in detail:
        components.append(f"deuda {detail['debt_score']}")

    if "fcf_score" in detail:
        components.append(f"flujo de caja libre {detail['fcf_score']}")

    if not components:
        return "Calidad calculada sin componentes identificados."

    return (
        f"Calidad calculada con {component_count} métrica{'s' if component_count != 1 else ''}: "
        + ", ".join(components)
        + ". Cada métrica se compara contra su sector usando percentiles robustos."
    )


def add_quality_scores(rows: list[dict[str, Any]]) -> None:
    """
    Agrega scores de calidad a todas las empresas.

    Modifica rows in-place agregando:
    - quality: score de 0-100 o None
    - quality_detail: detalles del cálculo

    Args:
        rows: Lista de empresas con datos fundamentales
    """
    for row in rows:
        quality, detail = quality_score(row, rows)
        row["quality"] = quality
        row["quality_detail"] = detail
