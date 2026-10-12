"""Tests para el módulo de quality scoring."""

from app.quality import (
    _percentile_rank,
    _robust_scale,
    _winsorize,
    quality_score,
)


def test_winsorize():
    """Test de winsorización de valores extremos."""
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]
    
    winsorized = _winsorize(values, lower_pct=0.1, upper_pct=0.9)
    
    # El valor 100 debe ser reemplazado por un valor más bajo
    assert max(winsorized) < 100
    assert min(winsorized) >= 1
    
    # Lista vacía
    assert _winsorize([]) == []


def test_percentile_rank():
    """Test del cálculo de percentil."""
    values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    
    # Valor en el medio
    percentile = _percentile_rank(50, values)
    assert 40 <= percentile <= 60
    
    # Valor al final
    percentile = _percentile_rank(100, values)
    assert percentile >= 90
    
    # Valor al inicio
    percentile = _percentile_rank(10, values)
    assert percentile <= 10
    
    # Lista vacía
    percentile = _percentile_rank(50, [])
    assert percentile == 50.0


def test_robust_scale():
    """Test del escalado robusto con percentiles."""
    values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    
    # Valor alto (mayor es mejor)
    score = _robust_scale(80, values, higher_is_better=True)
    assert score is not None
    assert 70 <= score <= 100
    
    # Valor bajo (menor es mejor, como deuda)
    score = _robust_scale(20, values, higher_is_better=False)
    assert score is not None
    assert 70 <= score <= 100
    
    # Con pocos datos
    score = _robust_scale(50, [10, 20], higher_is_better=True)
    assert score is None


def test_quality_score_insufficient_peers():
    """Test cuando no hay suficientes empresas para comparar."""
    row = {
        "market": "us",
        "sector": "technology",
        "operating_margin": 0.30,
        "net_margin": 0.20,
        "roe": 0.15,
        "debt_to_equity": 0.5,
        "fcf_yield": 0.05,
    }
    
    # Solo 2 pares (insuficientes)
    all_rows = [
        row,
        {"market": "us", "sector": "technology", "operating_margin": 0.25},
        {"market": "us", "sector": "technology", "operating_margin": 0.20},
    ]
    
    quality, detail = quality_score(row, all_rows)
    
    assert quality is None
    assert detail["reason"] == "insufficient_peers"
    assert detail["peer_count"] == 2


def test_quality_score_no_sector():
    """Test cuando no hay sector asignado."""
    row = {
        "market": "us",
        "sector": None,
        "operating_margin": 0.30,
    }
    
    quality, detail = quality_score(row, [row])
    
    assert quality is None
    assert detail["reason"] == "no_sector"


def test_quality_score_with_valid_data():
    """Test del cálculo de calidad con datos válidos."""
    row = {
        "market": "us",
        "sector": "technology",
        "operating_margin": 0.30,
        "net_margin": 0.20,
        "roe": 0.15,
        "debt_to_equity": 0.5,
        "fcf_yield": 0.05,
    }
    
    # Crear 10 pares con valores variados
    all_rows = [row]
    for i in range(10):
        all_rows.append(
            {
                "market": "us",
                "sector": "technology",
                "operating_margin": 0.10 + i * 0.02,
                "net_margin": 0.05 + i * 0.02,
                "roe": 0.05 + i * 0.01,
                "debt_to_equity": 0.3 + i * 0.05,
                "fcf_yield": 0.02 + i * 0.01,
            }
        )
    
    quality, detail = quality_score(row, all_rows)
    
    # Debe tener un score válido
    assert quality is not None
    assert 0 <= quality <= 100
    assert detail.get("component_count", 0) > 0
    
    # Debe tener scores individuales
    assert "operating_margin_score" in detail or "net_margin_score" in detail
