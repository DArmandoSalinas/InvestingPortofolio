from typing import Any


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _decimal(value: float, digits: int) -> str:
    return f"{value:.{digits}f}".replace(".", ",")


def _percent(value: float) -> str:
    return f"{_decimal(value * 100, 1)}%"


def _piece(label: str, value: float | None, missing: list[str], na: list[str], field: str) -> str | None:
    if field in na:
        return f"{label} no aplica"
    if field in missing or value is None:
        return f"falta {label}" if field in missing else None
    return f"{label} {_percent(value)}"


def growth_note(row: dict[str, Any]) -> str:
    missing = list(row.get("missing_fields") or [])
    revenue = _piece(
        "ingresos", _number(row.get("revenue_growth_yoy")), missing, [], "revenue_growth_yoy"
    )
    earnings = _piece(
        "utilidades", _number(row.get("earnings_growth_yoy")), missing, [], "earnings_growth_yoy"
    )
    parts = [part for part in (revenue, earnings) if part]
    if not parts:
        return "No hay crecimiento anual para esta emisora."
    if all(part.startswith("falta") for part in parts):
        return "Faltan el crecimiento de ingresos y el de utilidades."
    change = " y ".join(parts)
    return f"{change[0].upper()}{change[1:]} contra el año anterior. La escala va de −20% a +30%."


def value_note(row: dict[str, Any]) -> str:
    missing = list(row.get("missing_fields") or [])
    na = list(row.get("na_fields") or [])
    bits: list[str] = []
    for label, field, digits in (
        ("P/E", "pe", 1),
        ("P/S", "ps", 1),
        ("EV/EBITDA", "ev_ebitda", 1),
    ):
        if field in na:
            bits.append(f"{label} no aplica")
            continue
        if field in missing:
            bits.append(f"falta {label}")
            continue
        number = _number(row.get(field))
        if number is not None:
            bits.append(f"{label} {_decimal(number, digits)}")
    usable = any(not bit.startswith("falta") and "no aplica" not in bit for bit in bits)
    if row.get("value_reference") == "sp500_sector":
        bits.append("el sector en México tiene menos de 8 emisoras, así que la comparación usa el S&P 500")
    elif row.get("value_reference") == "local":
        bits.append("la comparación es dentro del mismo mercado y sector")
    elif row.get("value") is None and usable:
        bits.append("no hubo un grupo de al menos 8 emisoras para comparar")
    if not bits:
        return "No hay múltiplos para esta emisora."
    sentences = [f"{bit[0].upper()}{bit[1:]}" for bit in bits]
    return ". ".join(sentences) + "."


def momentum_note(row: dict[str, Any]) -> str:
    missing = list(row.get("missing_fields") or [])
    bits: list[str] = []
    for label, field in (
        ("63 sesiones", "return_3m"),
        ("126 sesiones", "return_6m"),
        ("252 sesiones", "return_12m"),
    ):
        number = _number(row.get(field))
        if field in missing or number is None:
            if field in missing:
                bits.append(f"faltan {label}")
            continue
        bits.append(f"{label} {_percent(number)}")
    ratio = _number(row.get("price_to_sma200"))
    if "price_to_sma200" in missing or ratio is None:
        if "price_to_sma200" in missing:
            bits.append("falta el precio contra la media de 200 días")
    else:
        bits.append(f"precio contra la media de 200 días {_decimal(ratio, 2)}")
    if not bits:
        return "No hay precios suficientes para el momentum."
    sentences = [f"{bit[0].upper()}{bit[1:]}" for bit in bits]
    return ". ".join(sentences) + "."
