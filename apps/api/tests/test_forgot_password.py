"""Restablecimiento público: solo invitados activos reciben contraseña temporal."""

from unittest.mock import Mock, patch

from app.main import forgot_password
from app.schemas import ForgotPassword


def test_forgot_password_skips_unknown_email() -> None:
    db = Mock()
    db.get_allowed.return_value = None
    settings = Mock(site_url="https://example.com", admin_email="admin@example.com")

    with patch("app.passwords.issue_temporary_password") as issue:
        result = forgot_password(ForgotPassword(email="nadie@example.com"), db, settings)

    assert result == {"ok": True}
    issue.assert_not_called()


def test_forgot_password_skips_inactive() -> None:
    db = Mock()
    db.get_allowed.return_value = {"email": "x@example.com", "active": False, "role": "member"}
    settings = Mock(site_url="https://example.com", admin_email="admin@example.com")

    with patch("app.passwords.issue_temporary_password") as issue:
        result = forgot_password(ForgotPassword(email="x@example.com"), db, settings)

    assert result == {"ok": True}
    issue.assert_not_called()


def test_forgot_password_issues_for_active_member() -> None:
    db = Mock()
    db.get_allowed.return_value = {"email": "x@example.com", "active": True, "role": "member"}
    settings = Mock(site_url="https://example.com", admin_email="admin@example.com")

    with patch("app.main.issue_temporary_password", create=True):
        with patch("app.passwords.issue_temporary_password") as issue:
            issue.return_value = {"temp_password": "Alpha-Beta-11", "mail": "smtp"}
            with patch("app.mailer.send_password_reset") as send:
                result = forgot_password(ForgotPassword(email="x@example.com"), db, settings)

    assert result == {"ok": True}
    issue.assert_called_once()
    assert issue.call_args.kwargs["email"] == "x@example.com"
    assert issue.call_args.kwargs["send"] is send
    db.update_profile.assert_called_once()
