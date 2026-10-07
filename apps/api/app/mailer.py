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
