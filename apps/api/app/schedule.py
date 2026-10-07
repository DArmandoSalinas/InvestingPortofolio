import asyncio
import threading
from datetime import date

from app.refresh_ranking import MONTERREY, refresh_and_store

_lock = threading.Lock()
_announced = False


def ranking_due(latest: date | None, calculated: bool, today: date) -> bool:
    return latest != today or not calculated


def run_refresh_if_due() -> None:
    global _announced
    if not _lock.acquire(blocking=False):
        print("el cálculo del ranking ya está en curso", flush=True)
        return
    try:
        from datetime import datetime

        from app.config import get_settings
        from app.db import DatabaseUnavailable, SupabaseRest

        today = datetime.now(MONTERREY).date()
        db = SupabaseRest(get_settings())
        try:
            latest, calculated = db.latest_ranking_state()
        except DatabaseUnavailable as exc:
            print(f"no se pudo revisar el ranking: {exc}", flush=True)
            return
        finally:
            db.close()
        if not ranking_due(latest, calculated, today):
            if not _announced:
                print(f"ranking {today.isoformat()} ya está calculado", flush=True)
                _announced = True
        else:
            _announced = False
            refresh_and_store()
        try:
            from app.signal_job import refresh_signals

            refresh_signals()
        except Exception as exc:
            print(f"las señales fallaron: {exc}", flush=True)
        try:
            from app.brief_job import refresh_brief

            refresh_brief()
        except Exception as exc:
            print(f"el resumen falló: {exc}", flush=True)
    finally:
        _lock.release()


async def refresh_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await asyncio.to_thread(run_refresh_if_due)
        except Exception as exc:
            print(f"el cálculo del ranking falló: {exc}", flush=True)
        try:
            await asyncio.wait_for(stop.wait(), timeout=30 * 60)
        except TimeoutError:
            continue
