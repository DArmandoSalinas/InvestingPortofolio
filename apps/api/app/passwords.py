"""Invitación con contraseña temporal y cambio obligatorio."""

from collections.abc import Callable

from app.auth_utils import generate_temp_password, is_strong_password
from app.db import EmailAlreadyRegistered


def issue_temporary_password(
    db,
    *,
    email: str,
    invited_by: str,
    site_url: str,
    send: Callable[[str, str, str], str],
    password: str | None = None,
) -> dict[str, str | bool]:
    """
    Crea o actualiza el usuario con una contraseña temporal legible,
    obliga a cambiarla y manda el correo. Si el correo falla, igual
    devuelve la contraseña para que el admin pueda copiarla.
    """
    address = email.strip().lower()
    temporary = password or generate_temp_password()
    profile = db.get_profile(address) or {}
    user_id = profile.get("user_id")
    created = False
    if user_id:
        db.update_auth_user_password(str(user_id), temporary)
    else:
        found = db.find_auth_user_id(address)
        if found:
            user_id = found
            db.update_auth_user_password(str(user_id), temporary)
        else:
            try:
                user_id = db.create_auth_user(
                    address,
                    temporary,
                    {"must_change_password": True},
                )
                created = True
            except EmailAlreadyRegistered:
                user_id = db.find_auth_user_id(address)
                if not user_id:
                    raise
                db.update_auth_user_password(str(user_id), temporary)
    db.update_profile(
        address,
        {"must_change_password": True, "active": True},
    )
    # Metadatos de invitación solamente: la contraseña queda en Supabase Auth
    # (hash) y se muestra una sola vez al admin vía la respuesta de la API.
    db.save_invitation(address, invited_by)
    try:
        mail = send(address, temporary, site_url)
    except ValueError:
        mail = "error"
    return {
        "email": address,
        "user_id": str(user_id),
        "temp_password": temporary,
        "mail": mail,
        "created": created,
    }


def change_password(db, *, user_id: str, email: str, new_password: str) -> None:
    ok, message = is_strong_password(new_password)
    if not ok:
        raise ValueError(message)
    db.update_auth_user_password(user_id, new_password)
    db.update_profile(email, {"must_change_password": False})
    db.mark_invitation_used(email)
