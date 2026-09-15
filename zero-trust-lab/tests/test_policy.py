import os
import sys
import tempfile


sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "backend"
    )
)

import app as application


def setup_function():
    application.DATABASE_PATH = os.path.join(
        tempfile.gettempdir(),
        "zero_trust_test.db"
    )

    try:
        os.remove(application.DATABASE_PATH)
    except FileNotFoundError:
        pass

    application.initialize_database()


def test_valid_access():
    result = application.evaluate_access(
        {
            "user_id": 2,
            "device_id": 2,
            "resource_id": 1,
            "mfa": "correcto",
            "segment": "SEG-03",
            "origin": "10.0.1.25"
        }
    )

    assert result["result"] == "PERMITIDO"


def test_invalid_mfa():
    result = application.evaluate_access(
        {
            "user_id": 2,
            "device_id": 2,
            "resource_id": 1,
            "mfa": "incorrecto",
            "segment": "SEG-03",
            "origin": "10.0.1.25"
        }
    )

    assert result["result"] == "DENEGADO"
    assert result["reason"] == "MFA inválido"


def test_insufficient_permission():
    result = application.evaluate_access(
        {
            "user_id": 2,
            "device_id": 2,
            "resource_id": 3,
            "mfa": "correcto",
            "segment": "SEG-03",
            "origin": "10.0.1.25"
        }
    )

    assert result["result"] == "DENEGADO"


def test_unauthorized_device():
    result = application.evaluate_access(
        {
            "user_id": 3,
            "device_id": 3,
            "resource_id": 1,
            "mfa": "correcto",
            "segment": "SEG-03",
            "origin": "10.0.1.25"
        }
    )

    assert result["result"] == "DENEGADO"


def test_suspended_user():
    result = application.evaluate_access(
        {
            "user_id": 4,
            "device_id": 2,
            "resource_id": 1,
            "mfa": "correcto",
            "segment": "SEG-03",
            "origin": "10.0.1.25"
        }
    )

    assert result["result"] == "DENEGADO"


def test_wrong_segment():
    result = application.evaluate_access(
        {
            "user_id": 2,
            "device_id": 2,
            "resource_id": 1,
            "mfa": "correcto",
            "segment": "SEG-01",
            "origin": "10.0.1.25"
        }
    )

    assert result["result"] == "DENEGADO"