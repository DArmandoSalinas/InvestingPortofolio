"""Invitación, contraseña temporal y cambio obligatorio, con la API de Auth simulada."""

import pytest

from app.auth_utils import generate_temp_password, is_strong_password
from app.db import EmailAlreadyRegistered
from app.passwords import change_password, issue_temporary_password


class FakeDb:
    def __init__(self) -> None:
        self.profiles: dict[str, dict] = {}
        self.auth: dict[str, dict] = {}
        self.invitations: dict[str, dict] = {}
        self.created: list[str] = []
        self.updated: list[str] = []

    def get_profile(self, email: str):
        return self.profiles.get(email)

    def find_auth_user_id(self, email: str):
        for user_id, user in self.auth.items():
            if user["email"] == email:
                return user_id
        return None

    def create_auth_user(self, email: str, password: str, metadata=None):
        if any(user["email"] == email for user in self.auth.values()):
            raise EmailAlreadyRegistered(email)
        user_id = f"user-{len(self.auth) + 1}"
        self.auth[user_id] = {"email": email, "password": password, "metadata": metadata or {}}
        self.profiles[email] = {"user_id": user_id, "active": True, "must_change_password": False}
        self.created.append(email)
        return user_id

    def update_auth_user_password(self, user_id: str, new_password: str) -> None:
        self.auth[user_id]["password"] = new_password
        self.updated.append(user_id)

    def update_profile(self, email: str, fields: dict) -> None:
        self.profiles.setdefault(email, {})
        self.profiles[email].update(fields)

    def save_invitation(self, email: str, temp_password: str, invited_by: str) -> None:
        self.invitations[email] = {
            "temp_password": temp_password,
            "invited_by": invited_by,
            "used_at": None,
        }

    def mark_invitation_used(self, email: str) -> None:
        if email in self.invitations:
            self.invitations[email]["used_at"] = "now"
            self.invitations[email]["temp_password"] = ""


def _send_ok(email: str, password: str, site: str) -> str:
    assert "@" in email
    assert password
    assert site.startswith("http")
    return "smtp"


def test_temporary_password_is_readable_and_is_not_the_email():
    email = "salinas.diegoarmando03@gmail.com"
    for _ in range(20):
        password = generate_temp_password()
        assert password != email
        assert email.split("@")[0] not in password.lower()
        left, middle, number = password.split("-")
        assert left[0].isupper() and middle[0].isupper()
        assert number.isdigit() and len(number) == 2
        ok, _ = is_strong_password(password)
        assert ok


def test_invite_creates_the_user_forces_a_change_and_emails_the_temporary_password():
    db = FakeDb()
    sent: list[tuple[str, str]] = []

    def send(email: str, password: str, site: str) -> str:
        sent.append((email, password))
        return _send_ok(email, password, site)

    result = issue_temporary_password(
        db,
        email="Nuevo@Estudio.local",
        invited_by="admin@estudio.local",
        site_url="https://inversion.example",
        send=send,
    )

    assert result["created"] is True
    assert result["email"] == "nuevo@estudio.local"
    assert result["mail"] == "smtp"
    assert db.profiles["nuevo@estudio.local"]["must_change_password"] is True
    assert sent == [("nuevo@estudio.local", result["temp_password"])]
    assert db.auth[str(result["user_id"])]["password"] == result["temp_password"]
    assert db.invitations["nuevo@estudio.local"]["used_at"] is None


def test_invite_of_an_existing_user_rotates_the_password_without_creating_another():
    db = FakeDb()
    db.auth["user-diego"] = {"email": "salinas.diegoarmando03@gmail.com", "password": "vieja"}
    db.profiles["salinas.diegoarmando03@gmail.com"] = {
        "user_id": "user-diego",
        "must_change_password": False,
    }

    result = issue_temporary_password(
        db,
        email="salinas.diegoarmando03@gmail.com",
        invited_by="bootstrap",
        site_url="https://inversion.example",
        send=_send_ok,
    )

    assert result["created"] is False
    assert db.created == []
    assert db.updated == ["user-diego"]
    assert db.auth["user-diego"]["password"] == result["temp_password"]
    assert db.profiles["salinas.diegoarmando03@gmail.com"]["must_change_password"] is True


def test_a_race_where_auth_already_has_the_email_updates_that_user():
    db = FakeDb()
    db.auth["user-9"] = {"email": "ana@estudio.local", "password": "vieja"}

    def create(email: str, password: str, metadata=None):
        raise EmailAlreadyRegistered(email)

    db.create_auth_user = create  # type: ignore[method-assign]

    result = issue_temporary_password(
        db,
        email="ana@estudio.local",
        invited_by="admin@estudio.local",
        site_url="https://inversion.example",
        send=_send_ok,
    )

    assert result["user_id"] == "user-9"
    assert db.auth["user-9"]["password"] == result["temp_password"]


def test_mail_failure_still_returns_the_temporary_password():
    db = FakeDb()

    def send(email: str, password: str, site: str) -> str:
        raise ValueError("smtp caído")

    result = issue_temporary_password(
        db,
        email="ana@estudio.local",
        invited_by="admin@estudio.local",
        site_url="https://inversion.example",
        send=send,
    )

    assert result["mail"] == "error"
    assert result["temp_password"]
    assert db.auth[str(result["user_id"])]["password"] == result["temp_password"]


def test_resend_replaces_the_previous_temporary_password():
    db = FakeDb()
    first = issue_temporary_password(
        db,
        email="ana@estudio.local",
        invited_by="admin@estudio.local",
        site_url="https://inversion.example",
        send=_send_ok,
        password="Alpha-Bravo-11",
    )
    change_password(
        db,
        user_id=str(first["user_id"]),
        email="ana@estudio.local",
        new_password="NuevaClave1",
    )
    assert db.profiles["ana@estudio.local"]["must_change_password"] is False
    assert db.invitations["ana@estudio.local"]["used_at"] == "now"

    second = issue_temporary_password(
        db,
        email="ana@estudio.local",
        invited_by="admin@estudio.local",
        site_url="https://inversion.example",
        send=_send_ok,
        password="Carta-Delta-22",
    )

    assert second["temp_password"] == "Carta-Delta-22"
    assert second["temp_password"] != first["temp_password"]
    assert db.auth[str(first["user_id"])]["password"] == "Carta-Delta-22"
    assert db.profiles["ana@estudio.local"]["must_change_password"] is True
    assert db.invitations["ana@estudio.local"]["used_at"] is None


def test_change_password_rejects_a_weak_one_and_keeps_the_temporary():
    db = FakeDb()
    issued = issue_temporary_password(
        db,
        email="ana@estudio.local",
        invited_by="admin@estudio.local",
        site_url="https://inversion.example",
        send=_send_ok,
        password="Alpha-Bravo-11",
    )
    with pytest.raises(ValueError, match="8 caracteres"):
        change_password(
            db,
            user_id=str(issued["user_id"]),
            email="ana@estudio.local",
            new_password="corta",
        )
    assert db.auth[str(issued["user_id"])]["password"] == "Alpha-Bravo-11"
    assert db.profiles["ana@estudio.local"]["must_change_password"] is True


def test_change_password_replaces_it_and_clears_the_flag():
    db = FakeDb()
    issued = issue_temporary_password(
        db,
        email="ana@estudio.local",
        invited_by="admin@estudio.local",
        site_url="https://inversion.example",
        send=_send_ok,
        password="Alpha-Bravo-11",
    )
    change_password(
        db,
        user_id=str(issued["user_id"]),
        email="ana@estudio.local",
        new_password="Plataforma1",
    )
    assert db.auth[str(issued["user_id"])]["password"] == "Plataforma1"
    assert db.profiles["ana@estudio.local"]["must_change_password"] is False
    assert db.invitations["ana@estudio.local"]["used_at"] == "now"
