import smtplib
from email.message import EmailMessage
from typing import Any

import httpx

from app.config import Settings, env_value


def smtp_configured() -> bool:
    return bool(env_value("SMTP_HOST") and env_value("SMTP_FROM"))


def mail_problem(text: str) -> str:
    lowered = text.lower()
    if "rate limit" in lowered or "over_email_send_rate_limit" in lowered:
        return "Se enviaron demasiados enlaces. Intenta más tarde."
    if "email_not_allowed" in lowered:
        return "Ese correo no está autorizado"
    return "No se pudo enviar el enlace"


def invite_user(settings: Settings, email: str) -> None:
    redirect = f"{settings.site_url.rstrip('/')}/auth/confirm?next=/bienvenida"
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }
    try:
        response = httpx.post(
            f"{settings.supabase_url}/auth/v1/invite",
            headers=headers,
            json={"email": email, "data": {}, "redirect_to": redirect},
            timeout=20,
        )
    except httpx.HTTPError:
        raise ValueError("No se pudo enviar la invitación") from None
    
    if response.status_code >= 300:
        raise ValueError(mail_problem(response.text))


def send_text(recipients: list[str], subject: str, text: str) -> str:
    people = [item.strip().lower() for item in recipients if item and "@" in item]
    if not people:
        raise ValueError("No hay correos activos para el envío")
    if smtp_configured():
        _smtp(people, subject, text)
        return "smtp"
    _mailpit(people, subject, text)
    return "local"


def send_invitation(settings: Settings, email: str) -> str:
    invite_user(settings, email)
    return "smtp" if smtp_configured() else "supabase"


def send_invitation(email: str, temp_password: str, site_url: str) -> str:
    """Envía correo de invitación con contraseña temporal."""
    body = f"""Has sido invitado a la plataforma de inversión.

Entra aquí: {site_url.rstrip('/')}/login

Tu correo: {email}
Contraseña temporal: {temp_password}

En tu primer inicio de sesión se te pedirá cambiar esta contraseña por una nueva y segura.

La invitación expira en 7 días.

---
Este es un correo automático de Inversión. Si no esperabas esta invitación, ignóralo."""
    
    return send_text([email], "Invitación a la plataforma de inversión", body)


def _smtp(recipients: list[str], subject: str, text: str) -> None:
    host = env_value("SMTP_HOST")
    port_text = env_value("SMTP_PORT") or "587"
    try:
        port = int(port_text)
    except ValueError:
        port = 587
    sender = env_value("SMTP_FROM")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(text)
    try:
        with smtplib.SMTP(host, port, timeout=20) as client:
            client.starttls()
            user = env_value("SMTP_USER")
            password = env_value("SMTP_PASSWORD")
            if user:
                client.login(user, password)
            client.send_message(message)
    except (OSError, smtplib.SMTPException):
        raise ValueError("No se pudo enviar el correo") from None


def _mailpit(recipients: list[str], subject: str, text: str) -> None:
    url = (env_value("MAILPIT_URL") or "http://127.0.0.1:54324").rstrip("/")
    payload: dict[str, Any] = {
        "From": {"Email": "estudio@localhost", "Name": "Inversión"},
        "To": [{"Email": item} for item in recipients],
        "Subject": subject,
        "Text": text,
    }
    try:
        response = httpx.post(f"{url}/api/v1/send", json=payload, timeout=10)
    except httpx.HTTPError:
        raise ValueError("No se pudo enviar el correo") from None
    if response.status_code >= 300:
        raise ValueError("No se pudo enviar el correo")
