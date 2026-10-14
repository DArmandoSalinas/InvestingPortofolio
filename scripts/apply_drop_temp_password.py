#!/usr/bin/env python3
"""Aplica el DROP de invitations.temp_password en Supabase (local o cloud).

Uso:
  # Local (Docker Supabase)
  python scripts/apply_drop_temp_password.py --local

  # Cloud con DATABASE_URL
  DATABASE_URL='postgresql://...' python scripts/apply_drop_temp_password.py

  # Cloud con service role vía Railway (requiere psycopg y DB password en DATABASE_URL)
  railway run --service api -- python scripts/apply_drop_temp_password.py
"""

from __future__ import annotations

import argparse
import os
import sys


SQL = """
alter table public.invitations drop column if exists temp_password;
comment on table public.invitations is
  'Tracking de invitaciones. La contraseña temporal no se almacena aquí; solo en Supabase Auth.';
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true", help="Usar postgres local de Supabase")
    args = parser.parse_args()
    url = (
        "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        if args.local
        else os.environ.get("DATABASE_URL", "").strip()
    )
    if not url:
        print("Falta DATABASE_URL (o usa --local).", file=sys.stderr)
        return 1
    try:
        import psycopg
    except ImportError:
        print("Instala psycopg: pip install psycopg[binary]", file=sys.stderr)
        return 1
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(SQL)
        conn.commit()
    print("OK: temp_password eliminada (si existía).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
