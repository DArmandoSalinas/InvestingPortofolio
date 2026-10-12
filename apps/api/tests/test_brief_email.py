"""Tests for brief email delivery with BRIEF_EMAIL_ENABLED flag."""
from datetime import date
from unittest.mock import Mock, patch

from app.brief_job import deliver_brief
from app.config import Settings


@patch("app.brief_job.SupabaseRest")
@patch("app.brief_job.get_settings")
def test_deliver_brief_disabled_by_default(mock_settings: Mock, mock_db_class: Mock) -> None:
    """deliver_brief no envía correo si BRIEF_EMAIL_ENABLED=false (default)."""
    settings = Settings(
        supabase_url="http://test.local",
        supabase_service_role_key="test-key",
        supabase_anon_key="test-anon",
        admin_email="admin@test.local",
        brief_email_enabled=False,  # Default
    )
    mock_settings.return_value = settings
    
    deliver_brief(date(2026, 10, 12))
    
    # No debería crear instancia de DB ni enviar nada
    mock_db_class.assert_not_called()


@patch("app.mailer.send_text")
@patch("app.brief_job.SupabaseRest")
@patch("app.brief_job.get_settings")
def test_deliver_brief_enabled(mock_settings: Mock, mock_db_class: Mock, mock_send: Mock) -> None:
    """deliver_brief envía correo si BRIEF_EMAIL_ENABLED=true."""
    settings = Settings(
        supabase_url="http://test.local",
        supabase_service_role_key="test-key",
        supabase_anon_key="test-anon",
        admin_email="admin@test.local",
        brief_email_enabled=True,
    )
    mock_settings.return_value = settings
    
    mock_db = Mock()
    mock_db_class.return_value = mock_db
    mock_db.get_brief.return_value = {
        "as_of": "2026-10-12",
        "headline": "Test Brief",
        "body": {"highlights": [], "movers": []},
        "emailed_at": None,
    }
    mock_db.list_allowed.return_value = [
        {"email": "user@test.com", "active": True}
    ]
    
    deliver_brief(date(2026, 10, 12))
    
    # Debería enviar correo
    mock_send.assert_called_once()
    assert "user@test.com" in mock_send.call_args[0][0]


@patch("app.brief_job.SupabaseRest")
@patch("app.brief_job.get_settings")
def test_deliver_brief_already_sent(mock_settings: Mock, mock_db_class: Mock) -> None:
    """deliver_brief no reenvía si ya tiene emailed_at."""
    settings = Settings(
        supabase_url="http://test.local",
        supabase_service_role_key="test-key",
        supabase_anon_key="test-anon",
        admin_email="admin@test.local",
        brief_email_enabled=True,
    )
    mock_settings.return_value = settings
    
    mock_db = Mock()
    mock_db_class.return_value = mock_db
    mock_db.get_brief.return_value = {
        "as_of": "2026-10-12",
        "headline": "Test Brief",
        "body": {},
        "emailed_at": "2026-10-12T09:00:00",  # Ya enviado
    }
    
    with patch("app.mailer.send_text") as mock_send:
        deliver_brief(date(2026, 10, 12))
        mock_send.assert_not_called()
