import pytest
from pydantic import ValidationError

from app.config import Settings


def _settings(**kwargs: object) -> Settings:
    # Ignora apps/api/.env para aislar la opcionalidad de ADMIN_EMAIL.
    return Settings(
        _env_file=None,
        supabase_url="http://127.0.0.1:54321",
        supabase_service_role_key="service",
        supabase_anon_key="anon",
        **kwargs,  # type: ignore[arg-type]
    )


def test_settings_accept_missing_admin_email(monkeypatch):
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    assert _settings().admin_email is None


def test_settings_treat_blank_admin_as_missing(monkeypatch):
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    assert _settings(admin_email="   ").admin_email is None


def test_settings_reject_invalid_admin_email(monkeypatch):
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    with pytest.raises(ValidationError):
        _settings(admin_email="not-an-email")


def test_settings_with_supabase_only_are_enough_for_ranking_db(monkeypatch):
    """refresh_ranking solo necesita las llaves de Supabase, no ADMIN_EMAIL."""
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    settings = _settings(admin_email=None)
    assert settings.supabase_url
    assert settings.admin_email is None
