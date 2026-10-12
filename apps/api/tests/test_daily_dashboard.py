"""Tests para el módulo del dashboard diario."""

from app.daily_dashboard import (
    analyze_market_context,
    analyze_ranking_changes,
    analyze_signals,
    generate_daily_dashboard,
    suggest_actions,
)


def test_analyze_market_context():
    """Test del análisis de contexto del mercado."""
    # Con cambios significativos
    spy_data = {"return": 0.03, "period": "en la última semana"}
    btc_data = {"return": -0.06, "period": "en los últimos 3 días"}
    
    insights = analyze_market_context(spy_data, btc_data)
    
    assert len(insights) >= 1
    assert any("S&P 500" in insight for insight in insights)
    assert any("Bitcoin" in insight for insight in insights)
    
    # Sin cambios significativos
    spy_data = {"return": 0.005, "period": "hoy"}
    btc_data = {"return": 0.01, "period": "hoy"}
    
    insights = analyze_market_context(spy_data, btc_data)
    
    assert len(insights) >= 1
    assert any("sin grandes movimientos" in insight.lower() for insight in insights)
    
    # Sin datos
    insights = analyze_market_context(None, None)
    assert len(insights) >= 1


def test_analyze_ranking_changes():
    """Test del análisis de cambios en el ranking."""
    current = [
        {
            "market": "us",
            "symbol": "AAPL",
            "name": "Apple",
            "composite": 85,
            "growth": 80,
            "value": 85,
            "momentum": 90,
            "quality": 88,
        },
        {
            "market": "us",
            "symbol": "MSFT",
            "name": "Microsoft",
            "composite": 78,
            "growth": 75,
            "value": 76,
            "momentum": 82,
            "quality": 80,
        },
    ]
    
    # Sin ranking previo
    insights = analyze_ranking_changes(current, None)
    
    assert len(insights) >= 1
    assert any("Apple" in insight or "Microsoft" in insight for insight in insights)
    
    # Con ranking previo y cambios grandes
    previous = [
        {
            "market": "us",
            "symbol": "AAPL",
            "name": "Apple",
            "composite": 65,  # Subió 20 puntos
        },
        {
            "market": "us",
            "symbol": "MSFT",
            "name": "Microsoft",
            "composite": 92,  # Bajó 14 puntos
        },
    ]
    
    insights = analyze_ranking_changes(current, previous)
    
    # Debe mencionar el gran cambio de Apple
    assert any("Apple" in insight and "subió" in insight for insight in insights)


def test_analyze_signals():
    """Test del análisis de señales."""
    # Sin señales abiertas
    signals = [
        {
            "name": "Apple",
            "setup": "impulso",
            "status": "target",
            "entry": 100,
            "target": 110,
        }
    ]
    
    insights = analyze_signals(signals, None)
    
    assert len(insights) >= 1
    assert any("no hay señales abiertas" in insight.lower() for insight in insights)
    
    # Con señales abiertas
    signals = [
        {
            "name": "Apple",
            "setup": "impulso",
            "status": "open",
            "entry": 100,
            "target": 110,
        },
        {
            "name": "Microsoft",
            "setup": "retroceso",
            "status": "open",
            "entry": 200,
            "target": 220,
        },
    ]
    
    insights = analyze_signals(signals, None)
    
    assert len(insights) >= 1
    assert any("señales abiertas" in insight.lower() for insight in insights)
    
    # Con métricas de desempeño
    performance = {
        "impulso": {"hit_rate": 0.65},
        "retroceso": {"hit_rate": 0.55},
    }
    
    insights = analyze_signals(signals, performance)
    
    assert any("65" in insight or "55" in insight for insight in insights)


def test_suggest_actions():
    """Test de sugerencias de acción."""
    ranking = [
        {
            "market": "us",
            "symbol": "AAPL",
            "name": "Apple",
            "composite": 85,
            "growth": 80,
            "quality": 88,
        },
        {
            "market": "us",
            "symbol": "MSFT",
            "name": "Microsoft",
            "composite": 78,
            "quality": 82,
        },
        {
            "market": "us",
            "symbol": "GOOGL",
            "name": "Alphabet",
            "composite": 76,
            "quality": 75,
        },
    ]
    
    signals = [
        {"name": "Tesla", "status": "open"}
    ]
    
    # Sin perfil
    actions = suggest_actions(None, ranking, signals)
    
    assert len(actions) >= 1
    assert any("Apple" in action or "Microsoft" in action or "Alphabet" in action for action in actions)
    
    # Con perfil conservador
    profile = {"risk": "bajo", "horizon_years": 3}
    
    actions = suggest_actions(profile, ranking, signals)
    
    assert len(actions) >= 1
    # Debe sugerir empresas de calidad
    assert any("calidad" in action.lower() for action in actions)
    
    # Con perfil agresivo
    profile = {"risk": "alto", "horizon_years": 10}
    
    actions = suggest_actions(profile, ranking, signals)
    
    assert len(actions) >= 1


def test_generate_daily_dashboard():
    """Test de generación del dashboard completo."""
    from datetime import date
    
    ranking_current = [
        {
            "market": "us",
            "symbol": "AAPL",
            "name": "Apple",
            "composite": 85,
            "growth": 80,
            "value": 85,
            "momentum": 90,
            "quality": 88,
        },
    ]
    
    signals = [
        {"name": "Tesla", "setup": "impulso", "status": "open"}
    ]
    
    performance = {
        "impulso": {"hit_rate": 0.65, "avg_net_return": 0.03}
    }
    
    spy_data = {"return": 0.02, "period": "hoy"}
    
    dashboard = generate_daily_dashboard(
        ranking_current=ranking_current,
        ranking_previous=None,
        signals=signals,
        performance=performance,
        spy_data=spy_data,
        as_of=date(2023, 10, 12),
    )
    
    assert dashboard["as_of"] == "2023-10-12"
    assert "insights" in dashboard
    assert len(dashboard["insights"]) >= 3
    assert len(dashboard["insights"]) <= 5
    assert dashboard["has_open_signals"] is True
    assert dashboard["top_company"] is not None
    assert dashboard["top_company"]["name"] == "Apple"
