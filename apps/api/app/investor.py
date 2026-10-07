from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

SLEEVE_IDS = ("cetes", "ahorro", "etf", "acciones", "crypto")
MONTERREY = ZoneInfo("America/Monterrey")
KNOWN_CRYPTO = {"BTC": "Bitcoin", "ETH": "Ethereum"}

SLEEVES: list[dict[str, str]] = [
    {
        "id": "cetes",
        "name": "CETES",
        "detail": "Deuda del gobierno federal a plazo corto.",
    },
    {
        "id": "ahorro",
        "name": "Ahorro",
        "detail": "Dinero en el banco, disponible. La tasa la pone cada banco.",
    },
    {
        "id": "etf",
        "name": "ETFs",
        "detail": "Una canasta. El referente es el S&P 500, y solo se muestra lo ya ocurrido.",
    },
    {
        "id": "acciones",
        "name": "Acciones",
        "detail": "Empresas sueltas. El ranking las ordena con puntuaciones, no con un rendimiento esperado.",
    },
    {
        "id": "crypto",
        "name": "Crypto",
        "detail": "El referente es Bitcoin, y solo se muestra lo ya ocurrido.",
    },
]


def fit_note(sleeve_id: str, risk: str, horizon_years: int) -> str:
    short = horizon_years < 3
    if sleeve_id in ("cetes", "ahorro"):
        return "Cabe en el plazo y en la tolerancia que declaraste."
    if sleeve_id == "etf":
        if risk == "bajo" and short:
            return "El plazo declarado es corto y la tolerancia es baja para una canasta de acciones."
        if short:
            return "El plazo declarado es corto para una canasta de acciones."
        if risk == "bajo":
            return "La tolerancia declarada es baja para dejar aquí la mayor parte."
        return "Cabe en el plazo que declaraste."
    if sleeve_id == "acciones":
        if short:
            return "El plazo declarado es corto para empresas sueltas."
        if risk == "bajo":
            return "La tolerancia declarada es más baja que el movimiento de una sola empresa."
        return "Cabe en el plazo que declaraste."
    if short or risk != "alto":
        return "Se mueve más que el resto. La tolerancia o el plazo declarados no la cubren del todo."
    return "Cabe en la tolerancia alta que declaraste. El movimiento sigue siendo mayor."


def spanned_return(bars: list[dict[str, Any]]) -> dict[str, Any] | None:
    if len(bars) < 2:
        return None
    first = _point(bars[0])
    last = _point(bars[-1])
    if first is None or last is None or first[1] <= 0:
        return None
    if (last[0] - first[0]).days < 340:
        return None
    target = last[0] - timedelta(days=365)
    chosen = first
    for bar in bars:
        point = _point(bar)
        if point is None:
            return None
        if point[0] <= target:
            chosen = point
        else:
            break
    if chosen[1] <= 0:
        return None
    return {
        "value": last[1] / chosen[1] - 1,
        "start": chosen[0].isoformat(),
        "end": last[0].isoformat(),
    }


def parse_allocation(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    rows = data.get("sleeves")
    if not isinstance(rows, list):
        return None
    weights: dict[str, int] = {}
    reasons: dict[str, str] = {}
    for item in rows:
        if not isinstance(item, dict):
            return None
        sleeve_id = item.get("id")
        if sleeve_id not in SLEEVE_IDS or sleeve_id in weights:
            return None
        weight = _whole(item.get("weight"))
        if weight is None or not 0 <= weight <= 100:
            return None
        weights[sleeve_id] = weight
        reasons[sleeve_id] = str(item.get("reason") or "").strip()
    if sum(weights.values()) != 100:
        return None
    return {
        "summary": str(data.get("summary") or "").strip(),
        "risk": str(data.get("risk") or "").strip(),
        "sleeves": [
            {"id": sleeve_id, "weight": weights[sleeve_id], "reason": reasons[sleeve_id]}
            for sleeve_id in SLEEVE_IDS
        ],
    }


def normalize_holding(
    asset_class: str,
    symbol: str,
    market: str | None,
    quantity: float,
    unit_cost: float,
    currency: str | None,
    opened_on: date,
    today: date | None = None,
) -> dict[str, Any]:
    if asset_class not in ("stock", "etf", "crypto", "cetes", "ahorro"):
        raise ValueError("Ese tipo de posición no existe")
    if quantity <= 0 or quantity != quantity or unit_cost <= 0 or unit_cost != unit_cost:
        raise ValueError("La cantidad y el costo tienen que ser mayores que cero")
    current = today or datetime.now(MONTERREY).date()
    if opened_on > current:
        raise ValueError("La fecha no puede ser posterior a hoy")
    if asset_class in ("cetes", "ahorro"):
        code = "CETES" if asset_class == "cetes" else "Ahorro"
        money = currency if currency in ("MXN", "USD") else "MXN"
        return {
            "asset_class": asset_class,
            "symbol": code,
            "name": code,
            "yahoo_symbol": None,
            "quantity": quantity,
            "unit_cost": unit_cost,
            "currency": money,
            "opened_on": opened_on.isoformat(),
        }
    cleaned = symbol.strip().upper().replace(" ", "")
    if asset_class == "crypto":
        cleaned = cleaned.removesuffix("-USD")
        if not _symbol_ok(cleaned):
            raise ValueError("Escribe el símbolo, por ejemplo BTC")
        return {
            "asset_class": "crypto",
            "symbol": cleaned,
            "name": KNOWN_CRYPTO.get(cleaned, cleaned),
            "yahoo_symbol": f"{cleaned}-USD",
            "quantity": quantity,
            "unit_cost": unit_cost,
            "currency": "USD",
            "opened_on": opened_on.isoformat(),
        }
    if market not in ("us", "mx"):
        raise ValueError("Indica si cotiza en EE. UU. o en México")
    if market == "mx":
        cleaned = cleaned.removesuffix(".MX")
        if not _symbol_ok(cleaned):
            raise ValueError("Escribe el símbolo de la emisora")
        yahoo = f"{cleaned}.MX"
        display = cleaned
        money = "MXN"
    else:
        display = cleaned.replace("-", ".")
        yahoo = display.replace(".", "-")
        if not _symbol_ok(yahoo):
            raise ValueError("Escribe el símbolo de la emisora")
        money = "USD"
    return {
        "asset_class": asset_class,
        "symbol": display,
        "name": display,
        "yahoo_symbol": yahoo,
        "quantity": quantity,
        "unit_cost": unit_cost,
        "currency": money,
        "opened_on": opened_on.isoformat(),
    }


def position_view(row: dict[str, Any], price: float | None, price_as_of: str | None) -> dict[str, Any]:
    quantity = float(row["quantity"])
    unit_cost = float(row["unit_cost"])
    cost = quantity * unit_cost
    traded = row.get("yahoo_symbol")
    if not traded:
        state = "carried"
        market_value: float | None = cost
        pnl = None
        price = None
        price_as_of = None
    elif price is None or price <= 0:
        state = "missing"
        market_value = None
        pnl = None
        price_as_of = None
    else:
        state = "market"
        market_value = quantity * price
        pnl = market_value / cost - 1 if cost else None
    return {
        "id": row["id"],
        "asset_class": row["asset_class"],
        "symbol": row["symbol"],
        "name": row["name"],
        "quantity": quantity,
        "unit_cost": unit_cost,
        "currency": row["currency"],
        "opened_on": row["opened_on"],
        "price": price,
        "price_as_of": price_as_of,
        "cost": cost,
        "market_value": market_value,
        "pnl": pnl,
        "price_state": state,
    }


def rollup(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for row in rows:
        bucket = groups.setdefault(
            row["currency"],
            {"cost": 0.0, "market": 0.0, "missing": 0},
        )
        bucket["cost"] += float(row["cost"])
        if row["price_state"] == "missing":
            bucket["missing"] += 1
        elif row["market_value"] is not None:
            bucket["market"] += float(row["market_value"])
    return [
        {
            "currency": currency,
            "cost": bucket["cost"],
            "market_value": None if bucket["missing"] else bucket["market"],
            "missing": bucket["missing"],
        }
        for currency, bucket in sorted(groups.items())
    ]


def market_sleeves(risk: str | None, horizon_years: int | None) -> list[dict[str, Any]]:
    from app.market_data import daily_bars
    from app.signals import completed_bars

    series: dict[str, dict[str, Any] | None] = {"etf": None, "crypto": None}
    for symbol, asset_class, sleeve_id in (("SPY", "stock", "etf"), ("BTC-USD", "crypto", "crypto")):
        try:
            series[sleeve_id] = spanned_return(completed_bars(daily_bars(symbol), asset_class))
        except Exception:
            series[sleeve_id] = None
    rows: list[dict[str, Any]] = []
    for sleeve in SLEEVES:
        figure = series.get(sleeve["id"])
        rows.append(
            {
                **sleeve,
                "fit": fit_note(sleeve["id"], risk, horizon_years) if risk and horizon_years else "",
                "return_value": None if figure is None else figure["value"],
                "return_start": None if figure is None else figure["start"],
                "return_end": None if figure is None else figure["end"],
            }
        )
    return rows


def allocation_facts(profile: dict[str, Any], sleeves: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "moneda": profile["currency"],
        "monto": profile["amount"],
        "aportacion_mensual": profile["monthly_contribution"],
        "plazo_anos": profile["horizon_years"],
        "meta": profile["goal"],
        "tolerancia": profile["risk"],
        "cetes_tasa": None,
        "casilleros": [
            {
                "id": sleeve["id"],
                "rendimiento_observado": sleeve["return_value"],
                "desde": sleeve["return_start"],
                "hasta": sleeve["return_end"],
                "encaje": sleeve["fit"],
            }
            for sleeve in sleeves
        ],
    }


def priced_positions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from app.market_data import daily_bars
    from app.signals import completed_bars

    views: list[dict[str, Any]] = []
    for row in rows:
        yahoo = row.get("yahoo_symbol")
        price: float | None = None
        price_as_of: str | None = None
        if yahoo:
            asset_class = "crypto" if row.get("asset_class") == "crypto" else "stock"
            try:
                close = last_close(completed_bars(daily_bars(str(yahoo)), asset_class))
            except Exception:
                close = None
            if close is not None:
                price, price_as_of = close
        views.append(position_view(row, price, price_as_of))
    return views


def last_close(bars: list[dict[str, Any]]) -> tuple[float, str] | None:
    if not bars:
        return None
    point = _point(bars[-1])
    if point is None or point[1] <= 0:
        return None
    return point[1], point[0].isoformat()


def _point(bar: dict[str, Any]) -> tuple[date, float] | None:
    raw = str(bar.get("time") or "")[:10]
    if len(raw) != 10:
        return None
    try:
        day = date.fromisoformat(raw)
        close = float(bar["close"])
    except (TypeError, ValueError):
        return None
    if close != close:
        return None
    return day, close


def _whole(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _symbol_ok(symbol: str) -> bool:
    if not symbol or len(symbol) > 12:
        return False
    return all(character.isalnum() or character in ".-" for character in symbol)
