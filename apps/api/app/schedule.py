import asyncio
import threading
import traceback
from datetime import date, datetime

from app.refresh_ranking import MONTERREY, refresh_and_store

_lock = threading.Lock()
_announced = False


def ranking_due(latest: date | None, calculated: bool, today: date) -> bool:
    return latest != today or not calculated


def log_timestamp() -> str:
    """Return formatted timestamp for logs."""
    return datetime.now(MONTERREY).isoformat()


def run_with_retry(job_name: str, func, max_retries: int = 2) -> None:
    """Run a job function with retry logic and detailed logging."""
    for attempt in range(max_retries):
        try:
            print(f"[{log_timestamp()}] {job_name}: intento {attempt + 1} de {max_retries}", flush=True)
            func()
            print(f"[{log_timestamp()}] {job_name}: completado exitosamente", flush=True)
            return
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {str(exc)}"
            print(f"[{log_timestamp()}] {job_name}: error - {error_msg}", flush=True)
            if attempt < max_retries - 1:
                print(f"[{log_timestamp()}] {job_name}: reintentando...", flush=True)
            else:
                print(f"[{log_timestamp()}] {job_name}: todos los intentos fallaron", flush=True)
                print(f"[{log_timestamp()}] trace:\n{traceback.format_exc()}", flush=True)


def run_refresh_if_due() -> None:
    global _announced
    if not _lock.acquire(blocking=False):
        print(f"[{log_timestamp()}] el cálculo del ranking ya está en curso", flush=True)
        return
    try:
        from app.config import get_settings
        from app.db import DatabaseUnavailable, SupabaseRest

        today = datetime.now(MONTERREY).date()
        db = SupabaseRest(get_settings())
        
        try:
            latest, calculated = db.latest_ranking_state()
        except DatabaseUnavailable as exc:
            print(f"[{log_timestamp()}] no se pudo revisar el ranking: {exc}", flush=True)
            return
        finally:
            db.close()
        
        if not ranking_due(latest, calculated, today):
            if not _announced:
                print(f"[{log_timestamp()}] ranking {today.isoformat()} ya está calculado", flush=True)
                _announced = True
        else:
            _announced = False
            print(f"[{log_timestamp()}] iniciando actualización del ranking para {today.isoformat()}", flush=True)
            run_with_retry("ranking", refresh_and_store)
        
        from app.signal_job import refresh_signals

        print(f"[{log_timestamp()}] iniciando actualización de señales", flush=True)
        run_with_retry("señales", refresh_signals)
        
        from app.brief_job import refresh_brief

        print(f"[{log_timestamp()}] iniciando generación del resumen", flush=True)
        run_with_retry("resumen", refresh_brief)
        
    finally:
        _lock.release()


async def refresh_loop(stop: asyncio.Event) -> None:
    print(f"[{log_timestamp()}] ciclo de actualización iniciado, revisando cada 30 minutos", flush=True)
    
    while not stop.is_set():
        try:
            await asyncio.to_thread(run_refresh_if_due)
        except Exception as exc:
            print(f"[{log_timestamp()}] error crítico en el ciclo de actualización: {exc}", flush=True)
            print(f"[{log_timestamp()}] trace:\n{traceback.format_exc()}", flush=True)
        try:
            await asyncio.wait_for(stop.wait(), timeout=30 * 60)
        except TimeoutError:
            continue
