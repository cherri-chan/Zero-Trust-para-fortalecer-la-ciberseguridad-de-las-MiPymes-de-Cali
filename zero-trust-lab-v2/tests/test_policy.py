import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import app as application


@pytest.fixture(autouse=True)
def isolated_database():
    old_path = application.DATABASE_PATH
    fd, path = tempfile.mkstemp(prefix="zero_trust_test_", suffix=".db")
    os.close(fd)
    os.remove(path)
    application.DATABASE_PATH = path
    application.initialize_database()

    yield

    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    application.DATABASE_PATH = old_path


def access(user_id, device_id, resource_id, mfa="correcto", segment="SEG-03"):
    return application.evaluate_access(
        {
            "user_id": user_id,
            "device_id": device_id,
            "resource_id": resource_id,
            "mfa": mfa,
            "segment": segment,
            "origin": "10.0.1.25",
        }
    )


def test_valid_access():
    result = access(2, 2, 1)
    assert result["result"] == "PERMITIDO"


def test_invalid_mfa():
    result = access(2, 2, 1, mfa="incorrecto")
    assert result["result"] == "DENEGADO"
    assert "MFA inválido" in result["reason"]


def test_insufficient_permission():
    result = access(2, 2, 3)
    assert result["result"] == "DENEGADO"
    assert "permisos" in result["reason"]


def test_unauthorized_device():
    result = access(3, 3, 1)
    assert result["result"] == "DENEGADO"
    assert "Dispositivo" in result["reason"]


def test_suspended_user():
    result = access(4, 4, 1)
    assert result["result"] == "DENEGADO"
    assert "Usuario suspendido" in result["reason"]


def test_wrong_segment():
    result = access(2, 2, 1, segment="SEG-01")
    assert result["result"] == "DENEGADO"
    assert "Segmento" in result["reason"]


def test_device_must_belong_to_user():
    result = access(2, 1, 1)
    assert result["result"] == "DENEGADO"
    assert "no pertenece al usuario" in result["reason"]


def test_mfa_must_be_enabled():
    connection = application.get_connection()
    connection.execute("UPDATE users SET mfa_enabled = 0 WHERE id = 2")
    connection.commit()
    connection.close()

    result = access(2, 2, 1)
    assert result["result"] == "DENEGADO"
    assert "MFA no habilitado" in result["reason"]


def test_inactive_policy_denies_access():
    connection = application.get_connection()
    connection.execute("UPDATE policies SET active = 0 WHERE code = 'POL-04'")
    connection.commit()
    connection.close()

    result = access(2, 2, 1)
    assert result["result"] == "DENEGADO"
    assert "POL-04" in result["reason"]


def test_missing_resource_denies_access():
    result = access(2, 2, 999)
    assert result["result"] == "DENEGADO"
    assert "Recurso no encontrado" in result["reason"]


def test_audit_event_is_saved():
    application.evaluate_access(
        {
            "user_id": 2,
            "device_id": 2,
            "resource_id": 1,
            "mfa": "correcto",
            "segment": "SEG-03",
            "origin": "10.0.1.25",
        }
    )

    events = application.query_rows(
        "SELECT * FROM audit_events ORDER BY id DESC"
    )
    assert len(events) == 1
    assert events[0]["result"] == "PERMITIDO"
