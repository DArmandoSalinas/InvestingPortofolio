from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.config import Settings, get_settings
from app.db import DatabaseUnavailable, InvalidSession, SupabaseRest
from app.schemas import UserContext

_db: SupabaseRest | None = None


def get_db(settings: Annotated[Settings, Depends(get_settings)]) -> SupabaseRest:
    global _db
    if _db is None:
        _db = SupabaseRest(settings)
    return _db


def close_db() -> None:
    global _db
    if _db is not None:
        _db.close()
        _db = None


def require_user(
    db: Annotated[SupabaseRest, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> UserContext:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Sesión inválida")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    try:
        user = db.get_user(token)
        email = (user.get("email") or "").lower()
        allowed = db.get_allowed(email)
    except InvalidSession:
        raise HTTPException(status_code=401, detail="Sesión inválida") from None
    except DatabaseUnavailable:
        raise HTTPException(status_code=503, detail="La base de datos no responde") from None
    if not email or not allowed or not allowed["active"]:
        raise HTTPException(status_code=403, detail="Este correo no tiene acceso")
    profile = db.get_profile(email)
    return UserContext(
        id=user["id"],
        email=email,
        role=allowed["role"],
        display_name=None if profile is None else profile.get("display_name"),
    )


def require_admin(user: Annotated[UserContext, Depends(require_user)]) -> UserContext:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para esto")
    return user
