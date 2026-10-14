import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, parseaddr
from typing import Any

import httpx

from app.config import Settings, env_value

logger = logging.getLogger(__name__)


def smtp_configured() -> bool:
    return bool(env_value("SMTP_HOST") and env_value("SMTP_FROM"))


def brevo_configured() -> bool:
    return bool(env_value("BREVO_API_KEY"))


def mail_problem(text: str) -> str:
    lowered = text.lower()
    if "rate limit" in lowered or "over_email_send_rate_limit" in lowered:
        return "Se enviaron demasiados enlaces. Intenta más tarde."
    if "email_not_allowed" in lowered:
        return "Ese correo no está autorizado"
    return "No se pudo enviar el enlace"


def signin_link(settings: Settings, email: str) -> str:
    redirect = f"{settings.site_url.rstrip('/')}/auth/callback"
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
    }
    last = ""
    for kind in ("magiclink", "invite"):
        try:
            response = httpx.post(
                f"{settings.supabase_url}/auth/v1/admin/generate_link",
                headers=headers,
                json={"type": kind, "email": email, "options": {"redirect_to": redirect}},
                timeout=20,
            )
        except httpx.HTTPError:
            raise ValueError("No se pudo enviar el enlace") from None
        if response.status_code < 300:
            link = str((response.json() or {}).get("action_link") or "")
            if link:
                return link
        last = response.text
    raise ValueError(mail_problem(last))


def send_text(recipients: list[str], subject: str, text: str) -> str:
    people = [item.strip().lower() for item in recipients if item and "@" in item]
    if not people:
        raise ValueError("No hay correos activos para el envío")
    if brevo_configured():
        _brevo(people, subject, text)
        return "brevo"
    if smtp_configured():
        _smtp(people, subject, text)
        return "smtp"
    _mailpit(people, subject, text)
    return "local"


def send_signin(settings: Settings, email: str) -> str:
    link = signin_link(settings, email)
    body = (
        "Usa este enlace para entrar a Inversión. Caduca en una hora.\n\n"
        f"{link}\n\n"
        "Si no pediste entrar, ignora este mensaje."
    )
    return send_text([email], "Tu enlace para entrar", body)


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


def send_password_reset(email: str, temp_password: str, site_url: str) -> str:
    """Envía correo de restablecimiento con contraseña temporal."""
    body = f"""Pediste restablecer tu acceso a Inversión.

Entra aquí: {site_url.rstrip('/')}/login

Tu correo: {email}
Contraseña temporal: {temp_password}

Al entrar se te pedirá cambiar esta contraseña por una nueva y segura.

Si no pediste restablecerla, ignora este mensaje y usa tu contraseña actual.

---
Este es un correo automático de Inversión."""

    return send_text([email], "Tu contraseña temporal de Inversión", body)


def _smtp_from_header(raw: str) -> str:
    name, addr = parseaddr(raw or "")
    if addr and name:
        # Gmail tolera mejor el From ASCII; evita cortes por acentos en el display name.
        safe_name = name.encode("ascii", "ignore").decode("ascii").strip() or "Inversion"
        return formataddr((safe_name, addr))
    return raw


def _smtp(recipients: list[str], subject: str, text: str) -> None:
    host = env_value("SMTP_HOST")
    port_text = env_value("SMTP_PORT") or "587"
    try:
        port = int(port_text)
    except ValueError:
        port = 587
    sender = _smtp_from_header(env_value("SMTP_FROM") or "")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(text)
    user = env_value("SMTP_USER")
    password = (env_value("SMTP_PASSWORD") or "").replace(" ", "")
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=20) as client:
                if user:
                    client.login(user, password)
                client.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=20) as client:
                client.ehlo()
                client.starttls()
                client.ehlo()
                if user:
                    client.login(user, password)
                client.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        logger.warning("SMTP falló (%s): %s", type(exc).__name__, str(exc)[:200])
        raise ValueError("No se pudo enviar el correo") from None


def _brevo(recipients: list[str], subject: str, text: str) -> None:
    """Envía correo usando la API HTTP de Brevo (SendinBlue)."""
    api_key = env_value("BREVO_API_KEY")
    sender_email = env_value("BREVO_SENDER_EMAIL") or "noreply@inversion.app"
    sender_name = env_value("BREVO_SENDER_NAME") or "Inversión"
    
    payload: dict[str, Any] = {
        "sender": {"email": sender_email, "name": sender_name},
        "to": [{"email": email} for email in recipients],
        "subject": subject,
        "textContent": text,
    }
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "accept": "application/json",
    }
    
    try:
        response = httpx.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers=headers,
            timeout=15,
        )
    except httpx.HTTPError:
        raise ValueError("No se pudo enviar el correo por Brevo") from None
    
    if response.status_code >= 300:
        error_text = response.text
        if "unauthorized" in error_text.lower() or "api_key" in error_text.lower():
            raise ValueError("La llave de Brevo no es válida") from None
        raise ValueError(f"No se pudo enviar el correo por Brevo: {error_text[:100]}") from None


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
