"""Disk cache and resume checkpoints for ranking refreshes."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def cache_dir() -> Path:
    raw = os.environ.get("RANKING_CACHE_DIR", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path(os.environ.get("TMPDIR", "/tmp")) / "investing-ranking-cache"


def _safe_name(symbol: str) -> str:
    return symbol.replace("/", "_").replace("\\", "_")


def symbol_path(kind: str, as_of: str, symbol: str) -> Path:
    return cache_dir() / as_of / kind / f"{_safe_name(symbol)}.json"


def load_json(path: Path) -> Any | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))


def load_closes(as_of: str, symbol: str) -> list[float] | None:
    data = load_json(symbol_path("closes", as_of, symbol))
    if not isinstance(data, list) or not data:
        return None
    values: list[float] = []
    for item in data:
        try:
            values.append(float(item))
        except (TypeError, ValueError):
            return None
    return values


def save_closes(as_of: str, symbol: str, closes: list[float]) -> None:
    if closes:
        save_json(symbol_path("closes", as_of, symbol), closes)


def load_fundamentals(as_of: str, symbol: str) -> dict[str, Any] | None:
    data = load_json(symbol_path("fundamentals", as_of, symbol))
    return data if isinstance(data, dict) else None


def save_fundamentals(as_of: str, symbol: str, facts: dict[str, Any]) -> None:
    save_json(symbol_path("fundamentals", as_of, symbol), facts)


def checkpoint_path(as_of: str) -> Path:
    return cache_dir() / as_of / "checkpoint.json"


def load_checkpoint(as_of: str) -> dict[str, Any]:
    data = load_json(checkpoint_path(as_of))
    if not isinstance(data, dict):
        return {"closes_done": [], "fundamentals_done": []}
    closes = data.get("closes_done") or []
    funds = data.get("fundamentals_done") or []
    return {
        "closes_done": [str(item) for item in closes],
        "fundamentals_done": [str(item) for item in funds],
    }


def mark_closes_done(as_of: str, symbols: list[str]) -> None:
    state = load_checkpoint(as_of)
    done = set(state["closes_done"])
    done.update(symbols)
    state["closes_done"] = sorted(done)
    save_json(checkpoint_path(as_of), state)


def mark_fundamentals_done(as_of: str, symbols: list[str]) -> None:
    state = load_checkpoint(as_of)
    done = set(state["fundamentals_done"])
    done.update(symbols)
    state["fundamentals_done"] = sorted(done)
    save_json(checkpoint_path(as_of), state)
