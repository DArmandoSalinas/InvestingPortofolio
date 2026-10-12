from datetime import date
from typing import Any

import httpx

from app.config import Settings

SNAPSHOT_SELECT = (
    "as_of,growth,value,momentum,composite,value_reference,calculated,"
    "missing_fields,na_fields,"
    "companies!inner(id,market,symbol,name,sector,currency)"
)


class InvalidSession(Exception):
    pass


class DatabaseUnavailable(Exception):
    pass


class SupabaseRest:
    def __init__(self, settings: Settings) -> None:
        self.url = settings.supabase_url.rstrip("/")
        self.service_key = settings.supabase_service_role_key
        self.anon_key = settings.supabase_anon_key
        self.client = httpx.Client(timeout=20)

    def close(self) -> None:
        self.client.close()

    def _service_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    def _request(
        self, method: str, path: str, timeout: float | None = None, **kwargs: Any
    ) -> httpx.Response:
        if timeout is not None:
            kwargs["timeout"] = timeout
        try:
            response = self.client.request(method, f"{self.url}{path}", **kwargs)
        except httpx.HTTPError as exc:
            raise DatabaseUnavailable from exc
        if response.status_code >= 500:
            raise DatabaseUnavailable(response.text)
        return response

    def get_user(self, jwt: str) -> dict[str, Any]:
        response = self._request(
            "GET",
            "/auth/v1/user",
            headers={"apikey": self.anon_key, "Authorization": f"Bearer {jwt}"},
        )
        if response.status_code != 200:
            raise InvalidSession
        return response.json()

    def get_allowed(self, email: str) -> dict[str, Any] | None:
        response = self._request(
            "GET",
            "/rest/v1/allowed_emails",
            headers=self._service_headers(),
            params={"email": f"eq.{email}", "select": "email,role,active"},
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None

    def list_allowed(self) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "/rest/v1/allowed_emails",
            headers=self._service_headers(),
            params={"select": "email,role,active", "order": "email.asc"},
        )
        response.raise_for_status()
        return response.json()

    def upsert_allowed(self, email: str, role: str, active: bool) -> dict[str, Any]:
        response = self._request(
            "POST",
            "/rest/v1/allowed_emails",
            headers=self._service_headers(
                {"Prefer": "resolution=merge-duplicates,return=representation"}
            ),
            params={"on_conflict": "email"},
            json={"email": email, "role": role, "active": active},
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0]

    def update_profile(self, email: str, fields: dict[str, Any]) -> None:
        if not fields:
            return
        response = self._request(
            "PATCH",
            "/rest/v1/profiles",
            headers=self._service_headers({"Prefer": "return=minimal"}),
            params={"email": f"eq.{email}"},
            json=fields,
        )
        response.raise_for_status()

    def get_profile(self, email: str) -> dict[str, Any] | None:
        response = self._request(
            "GET",
            "/rest/v1/profiles",
            headers=self._service_headers(),
            params={"email": f"eq.{email}", "select": "display_name,role,active"},
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None

    def latest_as_of(self) -> date | None:
        response = self._request(
            "GET",
            "/rest/v1/score_snapshots",
            headers=self._service_headers(),
            params={"select": "as_of", "order": "as_of.desc", "limit": "1"},
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return None
        return date.fromisoformat(rows[0]["as_of"])

    def latest_ranking_state(self) -> tuple[date | None, bool]:
        latest = self.latest_as_of()
        if latest is None:
            return None, False
        response = self._request(
            "GET",
            "/rest/v1/score_snapshots",
            headers=self._service_headers(),
            params={
                "select": "company_id",
                "as_of": f"eq.{latest.isoformat()}",
                "calculated": "eq.false",
                "limit": "1",
            },
        )
        response.raise_for_status()
        return latest, not response.json()

    def fetch_company(self, market: str, symbol: str) -> dict[str, Any] | None:
        response = self._request(
            "GET",
            "/rest/v1/companies",
            headers=self._service_headers(),
            params={
                "select": (
                    "id,market,symbol,name,sector,currency,yahoo_symbol,"
                    "score_snapshots(as_of,growth,value,momentum,composite,value_reference,"
                    "calculated,revenue_growth_yoy,earnings_growth_yoy,pe,ps,ev_ebitda,"
                    "return_3m,return_6m,return_12m,price_to_sma200,missing_fields,na_fields)"
                ),
                "market": f"eq.{market}",
                "symbol": f"eq.{symbol}",
                "limit": "1",
            },
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None

    def list_signals(self) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "/rest/v1/signals",
            headers=self._service_headers(),
            params={"select": "*", "order": "as_of.desc"},
        )
        response.raise_for_status()
        return response.json()

    def insert_signals(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        response = self._request(
            "POST",
            "/rest/v1/signals",
            headers=self._service_headers(
                {"Prefer": "resolution=ignore-duplicates,return=minimal"}
            ),
            params={"on_conflict": "yahoo_symbol,setup,as_of"},
            json=rows,
            timeout=60,
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])

    def update_signal(self, signal_id: str, fields: dict[str, Any]) -> None:
        response = self._request(
            "PATCH",
            "/rest/v1/signals",
            headers=self._service_headers({"Prefer": "return=minimal"}),
            params={"id": f"eq.{signal_id}"},
            json=fields,
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])

    def fetch_snapshots(
        self, as_of: date, market: str | None, sector: str | None
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {
            "select": SNAPSHOT_SELECT,
            "as_of": f"eq.{as_of.isoformat()}",
        }
        if market:
            params["companies.market"] = f"eq.{market}"
        if sector:
            params["companies.sector"] = f"eq.{sector}"
        response = self._request(
            "GET",
            "/rest/v1/score_snapshots",
            headers=self._service_headers(),
            params=params,
        )
        response.raise_for_status()
        return [flatten_snapshot(row) for row in response.json()]

    def upsert_companies(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        response = self._request(
            "POST",
            "/rest/v1/companies",
            headers=self._service_headers(
                {"Prefer": "resolution=merge-duplicates,return=minimal"}
            ),
            params={"on_conflict": "market,symbol"},
            json=rows,
            timeout=180,
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])

    def upsert_snapshots(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        response = self._request(
            "POST",
            "/rest/v1/score_snapshots",
            headers=self._service_headers(
                {"Prefer": "resolution=merge-duplicates,return=minimal"}
            ),
            params={"on_conflict": "company_id,as_of"},
            json=rows,
            timeout=180,
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])

    def calculated_as_of(self, before: date | None = None) -> date | None:
        params = {
            "select": "as_of",
            "calculated": "eq.true",
            "order": "as_of.desc",
            "limit": "1",
        }
        if before is not None:
            params["as_of"] = f"lt.{before.isoformat()}"
        response = self._request(
            "GET",
            "/rest/v1/score_snapshots",
            headers=self._service_headers(),
            params=params,
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return None
        return date.fromisoformat(rows[0]["as_of"])

    def get_brief(self, as_of: date) -> dict[str, Any] | None:
        response = self._request(
            "GET",
            "/rest/v1/morning_briefs",
            headers=self._service_headers(),
            params={"select": "*", "as_of": f"eq.{as_of.isoformat()}", "limit": "1"},
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None

    def latest_brief(self) -> dict[str, Any] | None:
        response = self._request(
            "GET",
            "/rest/v1/morning_briefs",
            headers=self._service_headers(),
            params={"select": "*", "order": "as_of.desc", "limit": "1"},
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None

    def insert_brief(self, row: dict[str, Any]) -> None:
        response = self._request(
            "POST",
            "/rest/v1/morning_briefs",
            headers=self._service_headers(
                {"Prefer": "resolution=ignore-duplicates,return=minimal"}
            ),
            params={"on_conflict": "as_of"},
            json=row,
            timeout=60,
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])

    def mark_brief_emailed(self, as_of: date) -> None:
        from datetime import datetime, timezone

        response = self._request(
            "PATCH",
            "/rest/v1/morning_briefs",
            headers=self._service_headers({"Prefer": "return=minimal"}),
            params={"as_of": f"eq.{as_of.isoformat()}"},
            json={"emailed_at": datetime.now(timezone.utc).isoformat()},
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])

    def list_push_subscriptions(self) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "/rest/v1/push_subscriptions",
            headers=self._service_headers(),
            params={"select": "endpoint,p256dh,auth"},
        )
        response.raise_for_status()
        return response.json()

    def upsert_push_subscription(
        self, user_id: str, endpoint: str, p256dh: str, auth: str
    ) -> None:
        response = self._request(
            "POST",
            "/rest/v1/push_subscriptions",
            headers=self._service_headers(
                {"Prefer": "resolution=merge-duplicates,return=minimal"}
            ),
            params={"on_conflict": "endpoint"},
            json={"user_id": user_id, "endpoint": endpoint, "p256dh": p256dh, "auth": auth},
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])

    def delete_push_subscription(self, endpoint: str) -> None:
        response = self._request(
            "DELETE",
            "/rest/v1/push_subscriptions",
            headers=self._service_headers({"Prefer": "return=minimal"}),
            params={"endpoint": f'eq."{endpoint}"'},
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])

    def get_investor_profile(self, user_id: str) -> dict[str, Any] | None:
        response = self._request(
            "GET",
            "/rest/v1/investor_profiles",
            headers=self._service_headers(),
            params={"select": "*", "user_id": f"eq.{user_id}", "limit": "1"},
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None

    def upsert_investor_profile(self, row: dict[str, Any]) -> dict[str, Any]:
        response = self._request(
            "POST",
            "/rest/v1/investor_profiles",
            headers=self._service_headers(
                {"Prefer": "resolution=merge-duplicates,return=representation"}
            ),
            params={"on_conflict": "user_id"},
            json=row,
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])
        rows = response.json()
        return rows[0]

    def list_holdings(self, user_id: str) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "/rest/v1/holdings",
            headers=self._service_headers(),
            params={
                "select": "*",
                "user_id": f"eq.{user_id}",
                "order": "opened_on.desc,symbol.asc",
            },
        )
        response.raise_for_status()
        return response.json()

    def insert_holding(self, row: dict[str, Any]) -> None:
        response = self._request(
            "POST",
            "/rest/v1/holdings",
            headers=self._service_headers({"Prefer": "return=minimal"}),
            json=row,
        )
        if response.status_code == 409 or "23505" in response.text:
            raise ValueError("Esa posición ya está registrada")
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])

    def delete_holding(self, user_id: str, holding_id: str) -> bool:
        response = self._request(
            "DELETE",
            "/rest/v1/holdings",
            headers=self._service_headers({"Prefer": "return=representation"}),
            params={"id": f"eq.{holding_id}", "user_id": f"eq.{user_id}"},
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])
        return bool(response.json())

    def get_signal_config(self) -> dict[str, Any] | None:
        response = self._request(
            "GET",
            "/rest/v1/signal_config",
            headers=self._service_headers(),
            params={"select": "*", "id": "eq.1", "limit": "1"},
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None

    def update_signal_config(self, fields: dict[str, Any]) -> None:
        response = self._request(
            "PATCH",
            "/rest/v1/signal_config",
            headers=self._service_headers({"Prefer": "return=minimal"}),
            params={"id": "eq.1"},
            json=fields,
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])

    def list_watchlist(self) -> list[dict[str, Any]]:
        response = self._request(
            "GET",
            "/rest/v1/watchlist",
            headers=self._service_headers(),
            params={"select": "*", "order": "asset_class.asc,symbol.asc"},
        )
        response.raise_for_status()
        return response.json()

    def upsert_watch_item(self, row: dict[str, Any]) -> None:
        response = self._request(
            "POST",
            "/rest/v1/watchlist",
            headers=self._service_headers(
                {"Prefer": "resolution=merge-duplicates,return=minimal"}
            ),
            params={"on_conflict": "yahoo_symbol"},
            json=row,
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])

    def set_watch_active(self, yahoo_symbol: str, active: bool) -> bool:
        response = self._request(
            "PATCH",
            "/rest/v1/watchlist",
            headers=self._service_headers({"Prefer": "return=representation"}),
            params={"yahoo_symbol": f"eq.{yahoo_symbol}"},
            json={"active": active},
        )
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])
        return bool(response.json())

    def ensure_admin(self, email: str) -> None:
        self.upsert_allowed(email, "admin", True)
        self.update_profile(email, {"role": "admin", "active": True})

    def create_auth_user(self, email: str, password: str, user_metadata: dict | None = None) -> str:
        """
        Crea un usuario en Supabase Auth usando Admin API.
        Retorna el user_id.
        """
        import json
        
        payload = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": user_metadata or {},
        }
        
        response = self._request(
            "POST",
            "/auth/v1/admin/users",
            headers=self._service_headers(),
            json=payload,
            timeout=30,
        )
        
        if response.status_code >= 400:
            raise DatabaseUnavailable(f"Error creando usuario: {response.text[:500]}")
        
        user = response.json()
        return user["id"]
    
    def update_auth_user_password(self, user_id: str, new_password: str) -> None:
        """Actualiza la contraseña de un usuario en Supabase Auth."""
        response = self._request(
            "PUT",
            f"/auth/v1/admin/users/{user_id}",
            headers=self._service_headers(),
            json={"password": new_password},
            timeout=30,
        )
        
        if response.status_code >= 400:
            raise DatabaseUnavailable(f"Error actualizando contraseña: {response.text[:500]}")
    
    def get_user_by_email(self, email: str) -> dict | None:
        """Obtiene un usuario de Supabase Auth por email."""
        # Supabase Admin API no tiene búsqueda directa por email
        # Usamos la tabla profiles como proxy
        profile = self.get_profile(email)
        if not profile:
            return None
        
        # Para obtener el user_id, necesitamos buscarlo en auth.users
        # Como no tenemos acceso directo, retornamos lo que tenemos
        return profile
    
    def save_invitation(self, email: str, temp_password: str, invited_by: str) -> None:
        """Guarda una invitación en la tabla de invitations."""
        from datetime import datetime, timezone, timedelta
        
        response = self._request(
            "POST",
            "/rest/v1/invitations",
            headers=self._service_headers(
                {"Prefer": "resolution=merge-duplicates,return=minimal"}
            ),
            params={"on_conflict": "email"},
            json={
                "email": email,
                "temp_password": temp_password,
                "invited_by": invited_by,
                "invited_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            },
        )
        
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])
    
    def mark_invitation_used(self, email: str) -> None:
        """Marca una invitación como usada."""
        from datetime import datetime, timezone
        
        response = self._request(
            "PATCH",
            "/rest/v1/invitations",
            headers=self._service_headers({"Prefer": "return=minimal"}),
            params={"email": f"eq.{email}"},
            json={"used_at": datetime.now(timezone.utc).isoformat()},
        )
        
        if response.status_code >= 400:
            raise DatabaseUnavailable(response.text[:2000])
    
    def get_invitation(self, email: str) -> dict | None:
        """Obtiene una invitación pendiente."""
        response = self._request(
            "GET",
            "/rest/v1/invitations",
            headers=self._service_headers(),
            params={
                "select": "*",
                "email": f"eq.{email}",
                "used_at": "is.null",
                "limit": "1",
            },
        )
        response.raise_for_status()
        rows = response.json()
        return rows[0] if rows else None

    def execute(self, query: str, params: dict[str, Any]) -> None:
        """Execute a raw SQL query (requires PostgREST RPC or direct connection)."""
        import json

        response = self._request(
            "POST",
            "/rest/v1/rpc/exec_sql",
            headers=self._service_headers(),
            json={"query": query, "params": json.dumps(params)},
        )
        if response.status_code >= 400:
            pass

    def list_scheduler_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent scheduler runs for admin visibility."""
        response = self._request(
            "GET",
            "/rest/v1/scheduler_runs",
            headers=self._service_headers(),
            params={"select": "*", "order": "started_at.desc", "limit": str(limit)},
        )
        response.raise_for_status()
        return response.json()

    def verify_digest_token(self, token: str) -> bool:
        """Verify a digest API token and update last_used_at."""
        from datetime import datetime, timezone

        response = self._request(
            "GET",
            "/rest/v1/digest_tokens",
            headers=self._service_headers(),
            params={"select": "token,active", "token": f"eq.{token}", "limit": "1"},
        )
        if response.status_code >= 400:
            return False
        rows = response.json()
        if not rows or not rows[0].get("active"):
            return False
        self._request(
            "PATCH",
            "/rest/v1/digest_tokens",
            headers=self._service_headers({"Prefer": "return=minimal"}),
            params={"token": f"eq.{token}"},
            json={"last_used_at": datetime.now(timezone.utc).isoformat()},
        )
        return True


def flatten_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    company = row["companies"]
    return {
        "id": company["id"],
        "market": company["market"],
        "symbol": company["symbol"],
        "name": company["name"],
        "sector": company["sector"],
        "currency": company["currency"],
        "growth": row["growth"],
        "value": row["value"],
        "momentum": row["momentum"],
        "composite": row["composite"],
        "value_reference": row["value_reference"],
        "missing_fields": row["missing_fields"] or [],
        "na_fields": row["na_fields"] or [],
        "calculated": bool(row.get("calculated")),
    }
