"""Tests for invitation and password authentication."""
from unittest.mock import Mock, patch

import httpx
import pytest

from app.config import Settings
from app.mailer import invite_user, mail_problem, send_invitation


def test_mail_problem_recognizes_rate_limit() -> None:
    assert "demasiados" in mail_problem("over_email_send_rate_limit")
    assert "demasiados" in mail_problem("Rate limit exceeded")


def test_mail_problem_recognizes_not_allowed() -> None:
    assert "autorizado" in mail_problem("email_not_allowed")


def test_mail_problem_default() -> None:
    assert "No se pudo" in mail_problem("Unknown error")


@patch("app.mailer.httpx.post")
def test_invite_user_success(mock_post: Mock) -> None:
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    settings = Settings(
        supabase_url="http://test.local",
        supabase_service_role_key="test-key",
        supabase_anon_key="test-anon",
        admin_email="admin@test.local",
        site_url="http://localhost:3000",
    )

    invite_user(settings, "user@test.local")

    assert mock_post.call_count == 1
    call_args = mock_post.call_args
    assert "/auth/v1/invite" in call_args[0][0]
    assert call_args[1]["json"]["email"] == "user@test.local"
    assert "/auth/confirm?next=/bienvenida" in call_args[1]["json"]["redirect_to"]


@patch("app.mailer.httpx.post")
def test_invite_user_http_error(mock_post: Mock) -> None:
    mock_post.side_effect = httpx.HTTPError("Network error")

    settings = Settings(
        supabase_url="http://test.local",
        supabase_service_role_key="test-key",
        supabase_anon_key="test-anon",
        admin_email="admin@test.local",
        site_url="http://localhost:3000",
    )

    with pytest.raises(ValueError, match="No se pudo enviar la invitación"):
        invite_user(settings, "user@test.local")


@patch("app.mailer.httpx.post")
def test_invite_user_api_error(mock_post: Mock) -> None:
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "email_not_allowed"
    mock_post.return_value = mock_response

    settings = Settings(
        supabase_url="http://test.local",
        supabase_service_role_key="test-key",
        supabase_anon_key="test-anon",
        admin_email="admin@test.local",
        site_url="http://localhost:3000",
    )

    with pytest.raises(ValueError, match="autorizado"):
        invite_user(settings, "user@test.local")


@patch("app.mailer.smtp_configured")
@patch("app.mailer.invite_user")
def test_send_invitation_with_smtp(mock_invite: Mock, mock_smtp: Mock) -> None:
    mock_smtp.return_value = True

    settings = Settings(
        supabase_url="http://test.local",
        supabase_service_role_key="test-key",
        supabase_anon_key="test-anon",
        admin_email="admin@test.local",
        site_url="http://localhost:3000",
    )

    result = send_invitation(settings, "user@test.local")

    assert result == "smtp"
    mock_invite.assert_called_once_with(settings, "user@test.local")


@patch("app.mailer.smtp_configured")
@patch("app.mailer.invite_user")
def test_send_invitation_without_smtp(mock_invite: Mock, mock_smtp: Mock) -> None:
    mock_smtp.return_value = False

    settings = Settings(
        supabase_url="http://test.local",
        supabase_service_role_key="test-key",
        supabase_anon_key="test-anon",
        admin_email="admin@test.local",
        site_url="http://localhost:3000",
    )

    result = send_invitation(settings, "user@test.local")

    assert result == "supabase"
    mock_invite.assert_called_once_with(settings, "user@test.local")
