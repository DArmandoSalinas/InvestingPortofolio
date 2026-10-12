"""
Tests unitarios para el motor de backtest con series sintéticas de resultado conocido.
"""

from app.backtest import (
    BacktestConfig,
    SignalResult,
    _calculate_metrics,
    _calculate_portfolio_drawdown,
)


def test_perfect_signals():
    """Serie sintética: 100% de acierto, todas alcanzan target."""
    results = [
        SignalResult(
            as_of="2024-01-01",
            asset_class="stock",
            symbol="TEST",
            setup="impulso",
            entry=100.0,
            stop=95.0,
            target=105.0,
            confidence=80,
            horizon_sessions=10,
            commission_rate=0.001,
            status="target",
            exit_price=105.0,
            exit_as_of="2024-01-05",
            gross_return=0.05,
            net_return=0.049,  # 5% - 0.1% comisión
            spy_return=0.01,
            btc_return=0.02,
        )
        for _ in range(10)
    ]

    config = BacktestConfig()
    metrics = _calculate_metrics(results, config)

    assert metrics.target_hit_rate == 1.0, f"Expected 1.0, got {metrics.target_hit_rate}"
    assert metrics.positive_return_rate == 1.0
    assert metrics.beats_spy_rate == 1.0
    assert metrics.targets == 10
    assert metrics.stops == 0
    assert metrics.expired == 0
    print("✓ test_perfect_signals passed")


def test_all_stops():
    """Serie sintética: 0% de acierto, todas tocan stop."""
    results = [
        SignalResult(
            as_of="2024-01-01",
            asset_class="stock",
            symbol="TEST",
            setup="retroceso",
            entry=100.0,
            stop=95.0,
            target=105.0,
            confidence=80,
            horizon_sessions=10,
            commission_rate=0.001,
            status="stop",
            exit_price=95.0,
            exit_as_of="2024-01-03",
            gross_return=-0.05,
            net_return=-0.051,  # -5% - 0.1% comisión
            spy_return=0.01,
            btc_return=0.02,
        )
        for _ in range(10)
    ]

    config = BacktestConfig()
    metrics = _calculate_metrics(results, config)

    assert metrics.target_hit_rate == 0.0
    assert metrics.positive_return_rate == 0.0
    assert metrics.beats_spy_rate == 0.0
    assert metrics.targets == 0
    assert metrics.stops == 10
    assert metrics.max_loss_per_trade == -0.051
    print("✓ test_all_stops passed")


def test_mixed_results():
    """Serie sintética: 60% acierto, 40% stops."""
    results = []

    # 6 targets
    for i in range(6):
        results.append(
            SignalResult(
                as_of=f"2024-01-{i+1:02d}",
                asset_class="stock",
                symbol="TEST",
                setup="impulso",
                entry=100.0,
                stop=95.0,
                target=105.0,
                confidence=80,
                horizon_sessions=10,
                commission_rate=0.001,
                status="target",
                exit_price=105.0,
                exit_as_of=f"2024-01-{i+5:02d}",
                gross_return=0.05,
                net_return=0.049,
                spy_return=0.02,
                btc_return=0.01,
            )
        )

    # 4 stops
    for i in range(4):
        results.append(
            SignalResult(
                as_of=f"2024-02-{i+1:02d}",
                asset_class="stock",
                symbol="TEST",
                setup="impulso",
                entry=100.0,
                stop=95.0,
                target=105.0,
                confidence=80,
                horizon_sessions=10,
                commission_rate=0.001,
                status="stop",
                exit_price=95.0,
                exit_as_of=f"2024-02-{i+3:02d}",
                gross_return=-0.05,
                net_return=-0.051,
                spy_return=0.02,
                btc_return=0.01,
            )
        )

    config = BacktestConfig()
    metrics = _calculate_metrics(results, config)

    assert metrics.target_hit_rate == 0.6
    assert metrics.targets == 6
    assert metrics.stops == 4
    # 6 con retorno positivo, 4 negativo
    assert metrics.positive_return_rate == 0.6
    # Todas le ganan a SPY (0.049 > 0.02 y -0.051 < 0.02, pero las que ganan son 6/10)
    # Wait, -0.051 NO gana a 0.02, así que beats_spy debería ser 6/10 = 0.6
    assert metrics.beats_spy_rate == 0.6
    print("✓ test_mixed_results passed")


def test_portfolio_drawdown_no_losses():
    """Portafolio sin pérdidas no debe tener drawdown."""
    results = [
        SignalResult(
            as_of=f"2024-01-{i+1:02d}",
            asset_class="stock",
            symbol="TEST",
            setup="impulso",
            entry=100.0,
            stop=95.0,
            target=105.0,
            confidence=80,
            horizon_sessions=10,
            commission_rate=0.001,
            status="target",
            exit_price=105.0,
            exit_as_of=f"2024-01-{i+5:02d}",
            gross_return=0.05,
            net_return=0.049,
            spy_return=0.02,
            btc_return=0.01,
        )
        for i in range(10)
    ]

    dd = _calculate_portfolio_drawdown(results, position_size=0.10, max_positions=10)

    assert dd == 0.0, f"Expected 0.0, got {dd}"
    print("✓ test_portfolio_drawdown_no_losses passed")


def test_portfolio_drawdown_with_loss():
    """Portafolio con una pérdida debe calcular drawdown correctamente."""
    results = [
        # 5 ganadoras
        *[
            SignalResult(
                as_of=f"2024-01-{i+1:02d}",
                asset_class="stock",
                symbol="TEST",
                setup="impulso",
                entry=100.0,
                stop=95.0,
                target=105.0,
                confidence=80,
                horizon_sessions=10,
                commission_rate=0.001,
                status="target",
                exit_price=105.0,
                exit_as_of=f"2024-01-{i+5:02d}",
                gross_return=0.05,
                net_return=0.049,
                spy_return=0.02,
                btc_return=0.01,
            )
            for i in range(5)
        ],
        # 1 perdedora grande
        SignalResult(
            as_of="2024-02-01",
            asset_class="stock",
            symbol="TEST",
            setup="impulso",
            entry=100.0,
            stop=90.0,
            target=105.0,
            confidence=80,
            horizon_sessions=10,
            commission_rate=0.001,
            status="stop",
            exit_price=90.0,
            exit_as_of="2024-02-03",
            gross_return=-0.10,
            net_return=-0.101,
            spy_return=0.02,
            btc_return=0.01,
        ),
    ]

    dd = _calculate_portfolio_drawdown(results, position_size=0.10, max_positions=10)

    # Con 10% por posición:
    # 5 operaciones con +4.9% c/u: equity ~ 1.0 * (1+0.0049)^5 ~ 1.0247
    # 1 operación con -10.1%: equity ~ 1.0247 * (1-0.0101) ~ 1.0144
    # El peak fue 1.0247, final 1.0144, drawdown ~ (1.0247-1.0144)/1.0247 ~ 1%
    # Esto debería ser un pequeño drawdown negativo
    assert dd is not None and dd < 0, f"Expected negative drawdown, got {dd}"
    assert dd > -0.02, f"Drawdown too large: {dd}"  # Should be small
    print(f"✓ test_portfolio_drawdown_with_loss passed (dd={dd:.4f})")


if __name__ == "__main__":
    print("Ejecutando tests unitarios del backtest...\n")
    test_perfect_signals()
    test_all_stops()
    test_mixed_results()
    test_portfolio_drawdown_no_losses()
    test_portfolio_drawdown_with_loss()
    print("\n✓ Todos los tests pasaron")
