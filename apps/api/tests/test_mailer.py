"""Tests for mailer with Brevo HTTP API support."""
from unittest.mock import Mock, patch

import httpx
import pytest

from app.mailer import brevo_configured, send_text, _brevo


@patch("app.mailer.env_value")
def test_brevo_configured_with_key(mock_env: Mock) -> None:
    mock_env.return_value = "test-brevo-key"
    assert brevo_configured() is True


@patch("app.mailer.env_value")
def test_brevo_configured_without_key(mock_env: Mock) -> None:
    mock_env.return_value = None
    assert brevo_configured() is False


@patch("app.mailer.httpx.post")
@patch("app.mailer.env_value")
def test_brevo_send_success(mock_env: Mock, mock_post: Mock) -> None:
    def env_side_effect(key: str) -> str | None:
        return {
            "BREVO_API_KEY": "test-key",
            "BREVO_SENDER_EMAIL": "test@example.com",
            "BREVO_SENDER_NAME": "Test Sender",
        }.get(key)
    
    mock_env.side_effect = env_side_effect
    
    mock_response = Mock()
    mock_response.status_code = 201
    mock_post.return_value = mock_response
    
    _brevo(["recipient@example.com"], "Test Subject", "Test body")
    
    assert mock_post.call_count == 1
    call_args = mock_post.call_args
    
    assert "https://api.brevo.com/v3/smtp/email" in call_args[0]
    assert call_args[1]["json"]["subject"] == "Test Subject"
    assert call_args[1]["json"]["textContent"] == "Test body"
    assert call_args[1]["json"]["to"] == [{"email": "recipient@example.com"}]
    assert call_args[1]["json"]["sender"]["email"] == "test@example.com"
    assert call_args[1]["headers"]["api-key"] == "test-key"


@patch("app.mailer.httpx.post")
@patch("app.mailer.env_value")
def test_brevo_send_http_error(mock_env: Mock, mock_post: Mock) -> None:
    mock_env.side_effect = lambda key: "test-key" if key == "BREVO_API_KEY" else None
    mock_post.side_effect = httpx.HTTPError("Network error")
    
    with pytest.raises(ValueError, match="No se pudo enviar el correo por Brevo"):
        _brevo(["recipient@example.com"], "Subject", "Body")


@patch("app.mailer.httpx.post")
@patch("app.mailer.env_value")
def test_brevo_send_api_error(mock_env: Mock, mock_post: Mock) -> None:
    mock_env.side_effect = lambda key: "test-key" if key == "BREVO_API_KEY" else None
    
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "unauthorized api_key"
    mock_post.return_value = mock_response
    
    with pytest.raises(ValueError, match="La llave de Brevo no es válida"):
        _brevo(["recipient@example.com"], "Subject", "Body")


@patch("app.mailer._brevo")
@patch("app.mailer.brevo_configured")
@patch("app.mailer.smtp_configured")
def test_send_text_prefers_brevo(mock_smtp: Mock, mock_brevo_cfg: Mock, mock_brevo: Mock) -> None:
    mock_brevo_cfg.return_value = True
    mock_smtp.return_value = False
    
    result = send_text(["test@example.com"], "Subject", "Body")
    
    assert result == "brevo"
    mock_brevo.assert_called_once_with(["test@example.com"], "Subject", "Body")


@patch("app.mailer._smtp")
@patch("app.mailer.brevo_configured")
@patch("app.mailer.smtp_configured")
def test_send_text_falls_back_to_smtp(mock_smtp_cfg: Mock, mock_brevo_cfg: Mock, mock_smtp: Mock) -> None:
    mock_brevo_cfg.return_value = False
    mock_smtp_cfg.return_value = True
    
    result = send_text(["test@example.com"], "Subject", "Body")
    
    assert result == "smtp"
    mock_smtp.assert_called_once()


@patch("app.mailer._mailpit")
@patch("app.mailer.brevo_configured")
@patch("app.mailer.smtp_configured")
def test_send_text_falls_back_to_mailpit(mock_smtp: Mock, mock_brevo: Mock, mock_mailpit: Mock) -> None:
    mock_brevo.return_value = False
    mock_smtp.return_value = False
    
    result = send_text(["test@example.com"], "Subject", "Body")
    
    assert result == "local"
    mock_mailpit.assert_called_once()
