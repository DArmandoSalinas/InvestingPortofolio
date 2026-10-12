"""
Carga las métricas de backtest en la tabla signal_performance.

Lee el resumen compacto por regla (out-of-sample) y hace upsert.
El comando es idempotente: volver a correrlo reemplaza las mismas filas.

  cd apps/api && uv run python -m app.load_backtest_performance
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.db import SupabaseRest

SUMMARY_PATH = Path(__file__).with_name("signal_performance.json")

ROW_FIELDS = (
    "setup",
    "total_signals",
    "targets",
    "stops",
    "expired",
    "hit_rate",
    "avg_net_return",
    "avg_gross_return",
    "avg_winner",
    "avg_loser",
    "win_loss_ratio",
)


def load_summary(path: Path | None = None) -> list[dict[str, Any]]:
    """Lee el resumen compacto y devuelve filas listas para upsert."""
    source = path or SUMMARY_PATH
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for rule in payload.get("rules") or []:
        setup = rule.get("setup")
        if setup not in ("impulso", "retroceso"):
            continue
        targets = int(rule["targets"])
        stops = int(rule["stops"])
        expired = int(rule["expired"])
        total = targets + stops + expired
        row: dict[str, Any] = {
            "setup": setup,
            "total_signals": total,
            "targets": targets,
            "stops": stops,
            "expired": expired,
            "hit_rate": rule.get("hit_rate"),
            "avg_net_return": rule.get("avg_net_return"),
            "avg_gross_return": rule.get("avg_gross_return"),
            "avg_winner": rule.get("avg_winner"),
            "avg_loser": rule.get("avg_loser"),
            "win_loss_ratio": rule.get("win_loss_ratio"),
        }
        rows.append({key: row[key] for key in ROW_FIELDS})
    rows.sort(key=lambda item: item["setup"])
    return rows


def compact_summary_from_results(results: dict[str, Any]) -> dict[str, Any]:
    """Arma el resumen compacto por regla a partir de un backtest en memoria."""
    oos = results.get("out_of_sample") or {}
    by_setup = oos.get("by_setup") or {}
    signals = oos.get("signals") or []
    rules: list[dict[str, Any]] = []
    for setup in ("impulso", "retroceso"):
        closed = [
            row
            for row in signals
            if row.get("setup") == setup and row.get("status") in {"target", "stop", "expired"}
        ]
        if not closed:
            metrics = by_setup.get(setup)
            if metrics is None:
                continue
            targets = int(getattr(metrics, "targets", 0))
            stops = int(getattr(metrics, "stops", 0))
            expired = int(getattr(metrics, "expired", 0))
            nets: list[float] = []
        else:
            targets = sum(1 for row in closed if row.get("status") == "target")
            stops = sum(1 for row in closed if row.get("status") == "stop")
            expired = sum(1 for row in closed if row.get("status") == "expired")
            nets = [float(row["net_return"]) for row in closed if row.get("net_return") is not None]
        total = targets + stops + expired
        winners = [value for value in nets if value > 0]
        losers = [value for value in nets if value < 0]
        metrics = by_setup.get(setup)
        hit_rate = getattr(metrics, "target_hit_rate", None) if metrics is not None else None
        avg_net = getattr(metrics, "avg_net_return", None) if metrics is not None else None
        if hit_rate is None and total:
            hit_rate = targets / total
        if avg_net is None and nets:
            avg_net = sum(nets) / len(nets)
        rules.append(
            {
                "setup": setup,
                "total_signals": total,
                "targets": targets,
                "stops": stops,
                "expired": expired,
                "hit_rate": hit_rate,
                "avg_net_return": avg_net,
                "avg_winner": (sum(winners) / len(winners)) if winners else None,
                "avg_loser": (sum(losers) / len(losers)) if losers else None,
                "win_loss_ratio": (
                    (sum(winners) / len(winners)) / abs(sum(losers) / len(losers))
                    if winners and losers
                    else None
                ),
                "beats_spy_rate": getattr(metrics, "beats_spy_rate", None) if metrics is not None else None,
            }
        )
    return {
        "period": "out-of-sample",
        "lookback_years": (results.get("config") or {}).get("lookback_years", 5),
        "rules": rules,
    }


def load_performance() -> None:
    """Carga las métricas de backtest en signal_performance. Idempotente."""
    print(f"Leyendo {SUMMARY_PATH.name}...", flush=True)
    first = load_summary()
    second = load_summary()
    if first != second:
        raise RuntimeError("El resumen compacto no es idempotente")
    if not first:
        print("No se encontraron métricas para cargar", flush=True)
        return

    print(f"Encontradas métricas para {len(first)} tipos de señal", flush=True)
    db = SupabaseRest(get_settings())
    try:
        db.upsert_signal_performance(first)
        for row in first:
            hit = row["hit_rate"]
            net = row["avg_net_return"]
            hit_text = f"{hit * 100:.1f}%" if hit is not None else "sin cifra"
            net_text = f"{net * 100:+.2f}%" if net is not None else "sin cifra"
            print(
                f"  {row['setup']}: {row['total_signals']} señales, "
                f"hit rate {hit_text}, retorno neto {net_text}",
                flush=True,
            )
        print("✓ Métricas guardadas en signal_performance", flush=True)
    finally:
        db.close()


if __name__ == "__main__":
    load_performance()
