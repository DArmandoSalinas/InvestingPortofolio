from app.load_backtest_performance import load_summary


def test_compact_summary_is_idempotent_and_totals_match():
    first = load_summary()
    second = load_summary()
    assert first == second
    assert {row["setup"] for row in first} == {"impulso", "retroceso"}
    for row in first:
        assert row["total_signals"] == row["targets"] + row["stops"] + row["expired"]
        assert row["total_signals"] > 0
