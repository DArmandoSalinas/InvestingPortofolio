"""Tests para el módulo de backtest."""

from app.backtest import (
    BacktestConfig,
    BacktestMetrics,
    SignalResult,
    _calculate_drawdown,
    _metrics_from_results,
    _split_data,
)


def test_split_data():
    """Test que la división in-sample/out-of-sample funciona correctamente."""
    data = [{"time": f"2020-{i:02d}-01", "close": 100 + i} for i in range(1, 11)]
    
    in_sample, out_of_sample = _split_data(data, ratio=0.6)
    
    assert len(in_sample) == 6
    assert len(out_of_sample) == 4
    assert in_sample[0]["time"] == "2020-01-01"
    assert out_of_sample[0]["time"] == "2020-07-01"


def test_calculate_drawdown():
    """Test del cálculo de drawdown."""
    # Sin drawdown
    cumulative = [1.0, 1.1, 1.2, 1.3]
    dd = _calculate_drawdown(cumulative)
    assert dd == 0.0
    
    # Con drawdown del 20%
    cumulative = [1.0, 1.5, 1.2, 1.0]
    dd = _calculate_drawdown(cumulative)
    assert dd < 0
    assert abs(dd - (-0.333)) < 0.01  # Aproximadamente -33.3%
    
    # Lista vacía
    dd = _calculate_drawdown([])
    assert dd is None


def test_metrics_from_results():
    """Test del cálculo de métricas agregadas."""
    results = [
        SignalResult(
            as_of="2023-01-01",
            asset_class="stock",
            symbol="AAPL",
            setup="impulso",
            entry=100.0,
            stop=95.0,
            target=110.0,
            confidence=70,
            horizon_sessions=10,
            commission_rate=0.001,
            status="target",
            exit_price=110.0,
            exit_as_of="2023-01-05",
            gross_return=0.10,
            net_return=0.098,
            spy_return=0.02,
            btc_return=0.05,
        ),
        SignalResult(
            as_of="2023-01-10",
            asset_class="stock",
            symbol="MSFT",
            setup="retroceso",
            entry=200.0,
            stop=190.0,
            target=220.0,
            confidence=65,
            horizon_sessions=10,
            commission_rate=0.001,
            status="stop",
            exit_price=190.0,
            exit_as_of="2023-01-12",
            gross_return=-0.05,
            net_return=-0.052,
            spy_return=-0.01,
            btc_return=0.02,
        ),
    ]
    
    metrics = _metrics_from_results(results)
    
    assert metrics.total_signals == 2
    assert metrics.targets == 1
    assert metrics.stops == 1
    assert metrics.hit_rate == 0.5
    assert metrics.avg_net_return is not None
    assert abs(metrics.avg_net_return - 0.023) < 0.01
    assert metrics.avg_winner is not None
    assert metrics.avg_loser is not None


def test_backtest_config():
    """Test de configuración del backtest."""
    config = BacktestConfig()
    
    assert config.stock_commission == 0.001
    assert config.crypto_commission == 0.002
    assert config.horizon_sessions == 10
    assert config.lookback_years == 5
    assert config.in_sample_ratio == 0.6
    
    # Configuración personalizada
    custom = BacktestConfig(
        lookback_years=3,
        in_sample_ratio=0.7,
    )
    
    assert custom.lookback_years == 3
    assert custom.in_sample_ratio == 0.7
