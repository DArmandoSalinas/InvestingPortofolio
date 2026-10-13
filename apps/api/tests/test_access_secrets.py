"""Acceso: la contraseña temporal no se persiste en invitations ni en el listado."""

from app.schemas import AccessEntry, AccessList


def test_access_list_entries_do_not_carry_temporary_passwords():
    board = AccessList(
        entries=[
            AccessEntry(
                email="admin@estudio.local",
                role="admin",
                active=True,
                protected=True,
                mail="",
                temporary_password="",
            )
        ]
    )
    for entry in board.entries:
        assert entry.temporary_password == ""


def test_create_response_may_include_password_once_but_not_as_stored_secret():
    """La API puede devolver temporary_password solo en create/resend para el flash."""
    entry = AccessEntry(
        email="a@b.co",
        role="member",
        active=True,
        temporary_password="Alpha-Bravo-11",
    )
    dumped = entry.model_dump()
    assert dumped["temporary_password"] == "Alpha-Bravo-11"
    assert "temp_password" not in dumped
