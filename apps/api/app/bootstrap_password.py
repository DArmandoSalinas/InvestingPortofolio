"""Genera la contraseña temporal de un usuario que ya existe.

Uso, con las variables de la API cargadas (en Railway: el shell del servicio):

    uv run python -m app.bootstrap_password --email salinas.diegoarmando03@gmail.com

Imprime la contraseña una sola vez. También intenta mandarla por SMTP.
"""

import argparse

from app.config import get_settings
from app.db import SupabaseRest
from app.mailer import send_invitation
from app.passwords import issue_temporary_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Contraseña temporal para un acceso existente.")
    parser.add_argument(
        "--email",
        default="salinas.diegoarmando03@gmail.com",
        help="Correo que ya está, o quedará, en la lista blanca.",
    )
    args = parser.parse_args()
    email = args.email.strip().lower()
    settings = get_settings()
    db = SupabaseRest(settings)
    try:
        db.upsert_allowed(email, "admin" if email == settings.admin_email else "member", True)
        result = issue_temporary_password(
            db,
            email=email,
            invited_by="bootstrap",
            site_url=settings.site_url,
            send=send_invitation,
        )
        role = "admin" if email == settings.admin_email else "member"
        db.update_profile(email, {"role": role, "active": True, "must_change_password": True})
    finally:
        db.close()
    print(f"correo: {email}")
    print(f"contraseña temporal: {result['temp_password']}")
    print(f"envío: {result['mail']}")
    print("En el primer inicio de sesión hay que cambiarla.")


if __name__ == "__main__":
    main()
