"""Resolve the monorepo root without hard-coding parent depth.

Works in the local checkout (`…/InvestingPortofolio/apps/api/app/…`),
in a Docker image that copies `apps/api` and `supabase` under `/app`,
and when `REPO_ROOT` / `INVESTING_REPO_ROOT` points at the checkout.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

_ENV_NAMES = ("REPO_ROOT", "ROOT_DIR", "INVESTING_REPO_ROOT")
_MARKERS = (
    ("supabase", "seed.sql"),
    ("supabase", "migrations"),
    ("package.json",),
    ("apps", "api"),
)


def _has_marker(candidate: Path) -> bool:
    for parts in _MARKERS:
        if (candidate.joinpath(*parts)).exists():
            return True
    return False


def _from_env() -> Path | None:
    for name in _ENV_NAMES:
        raw = os.environ.get(name, "").strip().strip('"').strip("'")
        if not raw:
            continue
        path = Path(raw).expanduser().resolve()
        if path.is_dir():
            return path
    return None


def walk_repo_root(start: Path) -> Path | None:
    """Walk `start` and its parents looking for a monorepo marker."""
    here = start.resolve()
    if here.is_file():
        here = here.parent
    for candidate in (here, *here.parents):
        if _has_marker(candidate):
            return candidate
    return None


def _resolve(start: Path) -> Path:
    found = _from_env()
    if found is not None:
        return found
    walked = walk_repo_root(start)
    if walked is not None:
        return walked
    # apps/api — usable when supabase/ is not in the image
    return Path(__file__).resolve().parents[1]


@lru_cache
def _cached_repo_root() -> Path:
    return _resolve(Path(__file__))


def repo_root(start: Path | None = None) -> Path:
    """Return the repository root, or the API package directory as last resort."""
    if start is not None:
        return _resolve(start)
    return _cached_repo_root()


def seed_sql_path(root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    return base / "supabase" / "seed.sql"


def clear_repo_root_cache() -> None:
    _cached_repo_root.cache_clear()
