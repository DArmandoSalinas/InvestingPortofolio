from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from app.scoring import highlights

NEW_YORK = ZoneInfo("America/New_York")
MOVER_LIMIT = 5


def session_date(now: datetime) -> date | None:
    local = now.astimezone(NEW_YORK)
    if (local.hour, local.minute) < (9, 0):
        return None
    return local.date()


def _key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("market") or ""), str(row.get("symbol") or ""))


def _ref(row: dict[str, Any]) -> dict[str, Any]:
    composite = row.get("composite")
    return {
        "market": row.get("market"),
        "symbol": row.get("symbol"),
        "name": row.get("name"),
        "composite": None if composite is None else int(composite),
    }


def ranking_brief(
    current: list[dict[str, Any]],
    previous: list[dict[str, Any]] | None,
    threshold: int,
) -> dict[str, Any]:
    current_highlights = highlights(current, threshold)
    if previous is None:
        return {
            "compared": False,
            "highlights": [_ref(row) for row in current_highlights],
            "entered": [],
            "left": [],
            "movers": [],
        }
    previous_highlights = highlights(previous, threshold)
    previous_keys = {_key(row) for row in previous_highlights}
    current_keys = {_key(row) for row in current_highlights}
    previous_by_key = {_key(row): row for row in previous}
    movers: list[dict[str, Any]] = []
    for row in current:
        before = previous_by_key.get(_key(row))
        if before is None or before.get("composite") is None or row.get("composite") is None:
            continue
        prior = int(before["composite"])
        latest = int(row["composite"])
        movers.append({**_ref(row), "before": prior, "after": latest, "delta": latest - prior})
    movers.sort(key=lambda item: abs(int(item["delta"])), reverse=True)
    return {
        "compared": True,
        "highlights": [_ref(row) for row in current_highlights],
        "entered": [_ref(row) for row in current_highlights if _key(row) not in previous_keys],
        "left": [_ref(row) for row in previous_highlights if _key(row) not in current_keys],
        "movers": movers[:MOVER_LIMIT],
    }


def brief_message(headline: str, body: dict[str, Any], site: str) -> str:
    lines = [headline.strip() or "Resumen del día", ""]
    highlights = [str(item.get("symbol")) for item in body.get("highlights") or [] if item.get("symbol")]
    entered = [str(item.get("symbol")) for item in body.get("entered") or [] if item.get("symbol")]
    left = [str(item.get("symbol")) for item in body.get("left") or [] if item.get("symbol")]
    if highlights:
        lines.append("Destacadas: " + ", ".join(highlights))
    if entered:
        lines.append("Entraron: " + ", ".join(entered))
    if left:
        lines.append("Salieron: " + ", ".join(left))
    movers = body.get("movers") or []
    if movers:
        lines.append("Cambios de la general:")
        for item in movers:
            symbol = item.get("symbol")
            if not symbol:
                continue
            lines.append(f"{symbol}: {item.get('before')} a {item.get('after')}")
    signals = body.get("signals") or []
    if signals:
        lines.append("Señales abiertas: " + ", ".join(str(item.get("symbol")) for item in signals if item.get("symbol")))
    lines.append("")
    lines.append(f"El resumen completo está en {site.rstrip('/')}/resumen")
    return "\n".join(lines)


def open_signals(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    picked = [row for row in rows if row.get("status") == "open"]
    picked.sort(key=lambda row: str(row.get("symbol") or ""))
    return [
        {
            "symbol": row.get("symbol"),
            "name": row.get("name"),
            "setup": row.get("setup"),
            "as_of": str(row.get("as_of"))[:10],
            "confidence": int(row.get("confidence") or 0),
            "asset_class": row.get("asset_class"),
        }
        for row in picked
    ]
