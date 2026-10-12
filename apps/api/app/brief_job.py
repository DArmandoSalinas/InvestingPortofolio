import json
from datetime import date, datetime
from typing import Any

from app.analyst import brief_reading
from app.brief import NEW_YORK, brief_message, open_signals, ranking_brief, session_date
from app.config import get_settings
from app.db import SupabaseRest
from app.push import send_brief_notifications


def refresh_brief(now: datetime | None = None) -> None:
    moment = now or datetime.now(NEW_YORK)
    as_of = session_date(moment)
    if as_of is None:
        return
    publish_brief(as_of)
    deliver_brief(as_of)


def deliver_brief(as_of: date) -> None:
    settings = get_settings()
    if not settings.brief_email_enabled:
        return
    
    db = SupabaseRest(settings)
    try:
        row = db.get_brief(as_of)
        if row is None or row.get("emailed_at"):
            return
        body = row.get("body") or {}
        if isinstance(body, str):
            body = json.loads(body)
        recipients = [item["email"] for item in db.list_allowed() if item.get("active") and item.get("email")]
        if not recipients:
            return
        from app.mailer import send_text

        headline = str(row.get("headline") or f"Resumen del {as_of.isoformat()}")
        try:
            send_text(recipients, headline, brief_message(headline, body, settings.site_url))
        except ValueError as exc:
            print(f"el resumen no se envió: {exc}", flush=True)
            return
        db.mark_brief_emailed(as_of)
        print(f"resumen enviado {as_of.isoformat()}", flush=True)
    finally:
        db.close()


def publish_brief(as_of: date) -> None:
    settings = get_settings()
    db = SupabaseRest(settings)
    try:
        if db.get_brief(as_of) is not None:
            return
        current_as_of = db.calculated_as_of()
        current = db.fetch_snapshots(current_as_of, None, None) if current_as_of else []
        previous_as_of = db.calculated_as_of(current_as_of) if current_as_of else None
        previous = db.fetch_snapshots(previous_as_of, None, None) if previous_as_of else None
        changes = ranking_brief(current, previous, settings.rank_highlight_min)
        signals = open_signals(db.list_signals())
        facts = {
            "sesion": as_of.isoformat(),
            "ranking_as_of": current_as_of.isoformat() if current_as_of else None,
            "previous_as_of": previous_as_of.isoformat() if previous_as_of else None,
            "comparado": changes["compared"],
            "altas": changes["highlights"],
            "entraron": changes["entered"],
            "salieron": changes["left"],
            "movimientos": changes["movers"],
            "senales_abiertas": signals,
        }
        reading = brief_reading(settings.xai_api_key, facts)
        headline = reading["headline"] or f"Resumen del {as_of.isoformat()}"
        db.insert_brief(
            {
                "as_of": as_of.isoformat(),
                "headline": headline,
                "ranking_as_of": current_as_of.isoformat() if current_as_of else None,
                "previous_as_of": previous_as_of.isoformat() if previous_as_of else None,
                "body": {
                    "compared": changes["compared"],
                    "highlights": changes["highlights"],
                    "entered": changes["entered"],
                    "left": changes["left"],
                    "movers": changes["movers"],
                    "signals": signals,
                },
                "reading_ranking": reading["ranking"],
                "reading_signals": reading["signals"],
                "reading_events": reading["events"],
            }
        )
        send_brief_notifications(settings, db, headline)
        print(f"resumen {as_of.isoformat()}", flush=True)
    finally:
        db.close()


def brief_payload(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    body = row.get("body") or {}
    if isinstance(body, str):
        body = json.loads(body)
    return {
        "as_of": row["as_of"],
        "headline": row.get("headline") or "",
        "ranking_as_of": row.get("ranking_as_of"),
        "previous_as_of": row.get("previous_as_of"),
        "compared": bool(body.get("compared")),
        "highlights": body.get("highlights") or [],
        "entered": body.get("entered") or [],
        "left": body.get("left") or [],
        "movers": body.get("movers") or [],
        "signals": body.get("signals") or [],
        "reading_ranking": row.get("reading_ranking") or "",
        "reading_signals": row.get("reading_signals") or "",
        "reading_events": row.get("reading_events") or "",
    }
