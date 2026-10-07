import json
from typing import Any

from app.config import Settings
from app.db import SupabaseRest


def send_brief_notifications(settings: Settings, db: SupabaseRest, headline: str) -> None:
    private_key = settings.vapid_private_key
    if not private_key:
        return
    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        print("avisos: falta pywebpush", flush=True)
        return
    payload = json.dumps(
        {"title": "Resumen", "body": headline, "url": "/resumen"},
        ensure_ascii=False,
    )
    for subscription in db.list_push_subscriptions():
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription["endpoint"],
                    "keys": {"p256dh": subscription["p256dh"], "auth": subscription["auth"]},
                },
                data=payload,
                vapid_private_key=private_key,
                vapid_claims={"sub": settings.vapid_subject},
            )
        except WebPushException as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in (404, 410):
                db.delete_push_subscription(str(subscription["endpoint"]))
            else:
                print(f"aviso no enviado: {status or exc}", flush=True)
        except Exception as exc:
            print(f"aviso no enviado: {exc}", flush=True)
