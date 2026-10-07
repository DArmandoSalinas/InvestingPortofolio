from app.scoring import apply_min, composite_of, highlights, is_highlight, sort_rows


def test_composite_rounds_half_up_for_thirds() -> None:
    assert composite_of(88, 76, 84) == 83
    assert composite_of(72, 71, 74) == 72
    assert composite_of(55, 62, 48) == 55
    assert composite_of(54, 61, 49) == 55
    assert composite_of(70, None, 60) is None


def test_sort_puts_nulls_last() -> None:
    rows = [
        {"composite": None, "growth": 10, "symbol": "a"},
        {"composite": 40, "growth": 90, "symbol": "b"},
        {"composite": 80, "growth": None, "symbol": "c"},
    ]
    assert [row["symbol"] for row in sort_rows(rows, None)] == ["c", "b", "a"]
    assert [row["symbol"] for row in sort_rows(rows, "growth")] == ["b", "a", "c"]


def test_min_score_hides_nulls_of_the_sorted_column() -> None:
    rows = [
        {"composite": None, "growth": 80},
        {"composite": 60, "growth": 40},
        {"composite": 75, "growth": 90},
    ]
    assert apply_min(rows, None, 70) == [rows[2]]
    assert apply_min(rows, "growth", 70) == [rows[0], rows[2]]


def test_highlight_needs_every_score() -> None:
    complete = {"growth": 70, "value": 70, "momentum": 70, "composite": 70}
    short = {"growth": 90, "value": 69, "momentum": 90, "composite": 83}
    incomplete = {"growth": 90, "value": None, "momentum": 90, "composite": None}
    assert is_highlight(complete, 70)
    assert not is_highlight(short, 70)
    assert not is_highlight(incomplete, 70)
    assert highlights([short, complete, incomplete], 70) == [complete]
