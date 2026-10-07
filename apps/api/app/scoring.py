import math
from typing import Any

SCORE_FIELDS = ("growth", "value", "momentum")
GROWTH_FIELDS = ("revenue_growth_yoy", "earnings_growth_yoy")
VALUE_FIELDS = ("pe", "ps", "ev_ebitda")
MOMENTUM_FIELDS = ("return_3m", "return_6m", "return_12m", "price_to_sma200")
RETURN_FIELDS = ("return_3m", "return_6m", "return_12m")

GROWTH_SCALE = (-0.20, 0.0, 0.30)
RETURN_SCALE = (-0.30, 0.0, 0.40)
SMA_SCALE = (0.70, 1.00, 1.30)
VALUE_MIN_GROUP = 8
TRADING_SESSIONS = {"return_3m": 63, "return_6m": 126, "return_12m": 252}


def composite_of(growth: int | None, value: int | None, momentum: int | None) -> int | None:
    if growth is None or value is None or momentum is None:
        return None
    return (growth + value + momentum + 1) // 3


def is_highlight(row: dict[str, Any], threshold: int) -> bool:
    return all(row[field] is not None and row[field] >= threshold for field in SCORE_FIELDS)


def sort_rows(rows: list[dict[str, Any]], style: str | None) -> list[dict[str, Any]]:
    field = style or "composite"
    return sorted(rows, key=lambda row: (row[field] is None, -(row[field] or 0)))


def apply_min(
    rows: list[dict[str, Any]], style: str | None, min_score: int | None
) -> list[dict[str, Any]]:
    if min_score is None:
        return rows
    field = style or "composite"
    return [row for row in rows if row[field] is not None and row[field] >= min_score]


def highlights(rows: list[dict[str, Any]], threshold: int) -> list[dict[str, Any]]:
    picked = [row for row in rows if is_highlight(row, threshold)]
    return sort_rows(picked, None)


def half_up(value: float) -> int:
    return math.floor(value + 0.5)


def average_half_up(scores: list[int]) -> int | None:
    if not scores:
        return None
    count = len(scores)
    return (sum(scores) + count // 2) // count


def map_scale(value: float, low: float, mid: float, high: float) -> int:
    if value <= low:
        return 0
    if value >= high:
        return 100
    if value == mid:
        return 50
    if value < mid:
        scaled = 50 * (value - low) / (mid - low)
    else:
        scaled = 50 + 50 * (value - mid) / (high - mid)
    return min(100, max(0, half_up(scaled)))


def trailing_return(closes: list[float], sessions: int) -> float | None:
    if sessions < 1 or len(closes) <= sessions:
        return None
    past = closes[-1 - sessions]
    latest = closes[-1]
    if past == 0 or not math.isfinite(past) or not math.isfinite(latest):
        return None
    return latest / past - 1


def price_to_sma200(closes: list[float]) -> float | None:
    if len(closes) < 200:
        return None
    window = closes[-200:]
    if any(not math.isfinite(price) for price in window):
        return None
    average = sum(window) / 200
    if average == 0:
        return None
    return window[-1] / average


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _component(raw: Any, scale: tuple[float, float, float]) -> tuple[int | None, bool]:
    number = _finite(raw)
    if number is None:
        return None, True
    return map_scale(number, *scale), False


def growth_score(
    revenue_growth_yoy: float | None, earnings_growth_yoy: float | None
) -> tuple[int | None, list[str]]:
    missing: list[str] = []
    scores: list[int] = []
    for field, raw in (
        ("revenue_growth_yoy", revenue_growth_yoy),
        ("earnings_growth_yoy", earnings_growth_yoy),
    ):
        score, absent = _component(raw, GROWTH_SCALE)
        if absent:
            missing.append(field)
        else:
            scores.append(score)  # type: ignore[arg-type]
    return average_half_up(scores), missing


def momentum_score(
    return_3m: float | None,
    return_6m: float | None,
    return_12m: float | None,
    price_to_sma200_value: float | None,
) -> tuple[int | None, list[str]]:
    missing: list[str] = []
    scores: list[int] = []
    for field, raw, scale in (
        ("return_3m", return_3m, RETURN_SCALE),
        ("return_6m", return_6m, RETURN_SCALE),
        ("return_12m", return_12m, RETURN_SCALE),
        ("price_to_sma200", price_to_sma200_value, SMA_SCALE),
    ):
        score, absent = _component(raw, scale)
        if absent:
            missing.append(field)
        else:
            scores.append(score)  # type: ignore[arg-type]
    return average_half_up(scores), missing


def _value_status(row: dict[str, Any]) -> dict[str, str]:
    status: dict[str, str] = {}
    pe = _finite(row.get("pe"))
    earnings_non_positive = bool(row.get("earnings_non_positive"))
    if earnings_non_positive or (pe is not None and pe <= 0):
        status["pe"] = "na"
    elif pe is None:
        status["pe"] = "missing"
    else:
        status["pe"] = "use"

    ps = _finite(row.get("ps"))
    status["ps"] = "use" if ps is not None and ps > 0 else "missing"

    ev = _finite(row.get("ev_ebitda"))
    if row.get("sector") == "financials":
        status["ev_ebitda"] = "na"
    elif ev is not None and ev > 0:
        status["ev_ebitda"] = "use"
    else:
        status["ev_ebitda"] = "missing"
    return status


def _cheaper_percentile(multiple: float, peers: list[float]) -> int | None:
    if not peers:
        return None
    higher = sum(1 for peer in peers if peer > multiple)
    count = len(peers)
    return (100 * higher + count // 2) // count


def _peer_multiples(peers: list[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for peer in peers:
        if _value_status(peer).get(field) != "use":
            continue
        number = _finite(peer.get(field))
        if number is not None:
            values.append(number)
    return values


def _value_pool(rows: list[dict[str, Any]], row: dict[str, Any]) -> tuple[list[dict[str, Any]] | None, str | None]:
    if row.get("sector") in (None, "", "unknown"):
        return None, None
    local = [
        other
        for other in rows
        if other.get("market") == row.get("market") and other.get("sector") == row.get("sector")
    ]
    if len(local) >= VALUE_MIN_GROUP:
        return [other for other in local if other is not row], "local"
    if row.get("market") == "mx":
        us = [
            other
            for other in rows
            if other.get("market") == "us" and other.get("sector") == row.get("sector")
        ]
        if len(us) >= VALUE_MIN_GROUP:
            return us, "sp500_sector"
    return None, None


def score_observations(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        growth, growth_missing = growth_score(
            row.get("revenue_growth_yoy"), row.get("earnings_growth_yoy")
        )
        momentum, momentum_missing = momentum_score(
            row.get("return_3m"),
            row.get("return_6m"),
            row.get("return_12m"),
            row.get("price_to_sma200"),
        )
        row["growth"] = growth
        row["momentum"] = momentum
        missing = [*growth_missing, *momentum_missing]
        na: list[str] = []
        status = _value_status(row)
        peers, reference = _value_pool(rows, row)
        contributions: list[int] = []
        for field in VALUE_FIELDS:
            kind = status[field]
            if kind == "na":
                na.append(field)
                row[field] = None
                continue
            if kind == "missing":
                missing.append(field)
                row[field] = None
                continue
            if peers is None:
                continue
            score = _cheaper_percentile(_finite(row[field]), _peer_multiples(peers, field))  # type: ignore[arg-type]
            if score is None:
                continue
            contributions.append(score)
        row["value"] = average_half_up(contributions)
        row["value_reference"] = reference if row["value"] is not None else None
        row["missing_fields"] = missing
        row["na_fields"] = na
        row["composite"] = composite_of(row["growth"], row["value"], row["momentum"])
