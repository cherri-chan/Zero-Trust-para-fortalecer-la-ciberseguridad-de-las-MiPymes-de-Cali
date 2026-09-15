import os
import sqlite3
import time
from datetime import datetime

from flask import Flask, jsonify, render_template, request


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "zero_trust.db")

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend", "templates")
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    active INTEGER NOT NULL,
    mfa_enabled INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY,
    identifier TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    operating_system TEXT NOT NULL,
    status TEXT NOT NULL,
    authorized INTEGER NOT NULL,
    posture TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    segment TEXT NOT NULL,
    sensitivity TEXT NOT NULL,
    required_role TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    priority INTEGER NOT NULL,
    active INTEGER NOT NULL,
    action TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_name TEXT NOT NULL,
    device_name TEXT NOT NULL,
    resource_name TEXT NOT NULL,
    origin TEXT NOT NULL,
    result TEXT NOT NULL,
    reason TEXT NOT NULL,
    policy TEXT NOT NULL,
    severity TEXT NOT NULL,
    decision_ms REAL NOT NULL
);
"""


def get_connection():
    os.makedirs(DATABASE_DIR, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def query_rows(sql, parameters=()):
    connection = get_connection()

    rows = [
        dict(row)
        for row in connection.execute(sql, parameters).fetchall()
    ]

    connection.close()

    return rows


def initialize_database():
    connection = get_connection()
    connection.executescript(SCHEMA)

    existing_users = connection.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    if existing_users == 0:
        connection.executemany(
            """
            INSERT INTO users
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    1,
                    "Carlos Pérez",
                    "carlos@empresa.local",
                    "Administrador",
                    1,
                    1
                ),
                (
                    2,
                    "Ana Rodríguez",
                    "ana@empresa.local",
                    "Operativo",
                    1,
                    1
                ),
                (
                    3,
                    "Usuario externo",
                    "externo@empresa.local",
                    "Externo",
                    1,
                    1
                ),
                (
                    4,
                    "Cuenta suspendida",
                    "suspendida@empresa.local",
                    "Operativo",
                    0,
                    1
                )
            ]
        )

        connection.executemany(
            """
            INSERT INTO devices
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    1,
                    "PC-ADM-001",
                    1,
                    "Portátil",
                    "Windows",
                    "Activo",
                    1,
                    "Conforme"
                ),
                (
                    2,
                    "PC-OP-002",
                    2,
                    "Escritorio",
                    "Linux",
                    "Activo",
                    1,
                    "Conforme"
                ),
                (
                    3,
                    "MOV-EXT-003",
                    3,
                    "Móvil",
                    "Android",
                    "Bloqueado",
                    0,
                    "No conforme"
                )
            ]
        )

        connection.executemany(
            """
            INSERT INTO resources
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    1,
                    "Aplicación empresarial",
                    "Aplicación",
                    "SEG-03",
                    "Media",
                    "Operativo"
                ),
                (
                    2,
                    "Servidor de archivos",
                    "Archivos",
                    "SEG-03",
                    "Alta",
                    "Operativo"
                ),
                (
                    3,
                    "Base de datos protegida",
                    "Base de datos",
                    "SEG-03",
                    "Crítica",
                    "Administrador"
                )
            ]
        )

        connection.executemany(
            """
            INSERT INTO policies
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    1,
                    "POL-01",
                    "Identidad y MFA válidos",
                    1,
                    1,
                    "PERMITIR"
                ),
                (
                    2,
                    "POL-02",
                    "Dispositivo autorizado y conforme",
                    2,
                    1,
                    "PERMITIR"
                ),
                (
                    3,
                    "POL-03",
                    "Rol compatible con el recurso",
                    3,
                    1,
                    "PERMITIR"
                ),
                (
                    4,
                    "POL-04",
                    "Segmento autorizado",
                    4,
                    1,
                    "PERMITIR"
                )
            ]
        )

    connection.commit()
    connection.close()


def evaluate_access(payload, save_event=True):
    start_time = time.perf_counter()

    connection = get_connection()

    user = connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (payload.get("user_id"),)
    ).fetchone()

    device = connection.execute(
        "SELECT * FROM devices WHERE id = ?",
        (payload.get("device_id"),)
    ).fetchone()

    resource = connection.execute(
        "SELECT * FROM resources WHERE id = ?",
        (payload.get("resource_id"),)
    ).fetchone()

    result = "DENEGADO"
    reason = ""
    policy = ""
    severity = "Alta"

    checks = []

    # 1. Identidad
    if user is None:
        checks.append(("Identidad", False))
        reason = "Identidad no encontrada"
        policy = "POL-01"
    elif not user["active"]:
        checks.append(("Identidad", False))
        reason = "Usuario suspendido"
        policy = "POL-01"
    else:
        checks.append(("Identidad", True))

    # 2. MFA
    mfa_valid = payload.get("mfa") == "correcto"
    checks.append(("MFA", mfa_valid))

    if not mfa_valid:
        reason = "MFA inválido"
        policy = "POL-01"

    # 3. Dispositivo
    device_valid = False

    if device is not None:
        device_valid = (
            bool(device["authorized"])
            and device["status"] == "Activo"
            and device["posture"] == "Conforme"
        )

    checks.append(("Dispositivo", device_valid))

    if not device_valid:
        reason = "Dispositivo no autorizado o postura no conforme"
        policy = "POL-02"

    # 4. Rol y segmento
    role_valid = False
    segment_valid = False

    if (
        user is not None
        and device is not None
        and resource is not None
        and user["active"]
        and mfa_valid
        and device_valid
    ):
        role_valid = (
            user["role"] == resource["required_role"]
            or user["role"] == "Administrador"
        )

        segment_valid = (
            payload.get("segment") == resource["segment"]
        )

        checks.append(("Rol", role_valid))
        checks.append(("Política/segmento", segment_valid))

        if not role_valid:
            reason = "El usuario no posee permisos para el recurso"
            policy = "POL-03"

        elif not segment_valid:
            reason = "Segmento de red no autorizado"
            policy = "POL-04"

        else:
            result = "PERMITIDO"
            reason = "Todas las condiciones fueron verificadas"
            policy = (
                "POL-01 + POL-02 + POL-03 + POL-04"
            )
            severity = "Baja"

    decision_time = round(
        (time.perf_counter() - start_time) * 1000,
        3
    )

    event = {
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "user_name": user["name"] if user else "Desconocido",
        "device_name": (
            device["identifier"] if device else "Desconocido"
        ),
        "resource_name": (
            resource["name"] if resource else "Desconocido"
        ),
        "origin": payload.get("origin", "SEG-01"),
        "result": result,
        "reason": reason,
        "policy": policy,
        "severity": severity,
        "decision_ms": decision_time
    }

    if save_event:
        connection.execute(
            """
            INSERT INTO audit_events
            (
                timestamp,
                user_name,
                device_name,
                resource_name,
                origin,
                result,
                reason,
                policy,
                severity,
                decision_ms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["timestamp"],
                event["user_name"],
                event["device_name"],
                event["resource_name"],
                event["origin"],
                event["result"],
                event["reason"],
                event["policy"],
                event["severity"],
                event["decision_ms"]
            )
        )

        connection.commit()

    connection.close()

    return {
        "result": result,
        "reason": reason,
        "policy": policy,
        "severity": severity,
        "decision_ms": decision_time,
        "checks": [
            {
                "name": name,
                "ok": status
            }
            for name, status in checks
        ],
        "event": event
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/api/data")
def get_data():
    users = query_rows(
        "SELECT * FROM users ORDER BY id"
    )

    devices = query_rows(
        """
        SELECT
            devices.*,
            users.name AS user_name
        FROM devices
        LEFT JOIN users
            ON users.id = devices.user_id
        ORDER BY devices.id
        """
    )

    resources = query_rows(
        "SELECT * FROM resources ORDER BY id"
    )

    policies = query_rows(
        "SELECT * FROM policies ORDER BY priority"
    )

    events = query_rows(
        """
        SELECT *
        FROM audit_events
        ORDER BY id DESC
        LIMIT 50
        """
    )

    stats = {
        "active_users": sum(
            user["active"] for user in users
        ),
        "authorized_devices": sum(
            device["authorized"] for device in devices
        ),
        "allowed_requests": len([
            event for event in events
            if event["result"] == "PERMITIDO"
        ]),
        "denied_requests": len([
            event for event in events
            if event["result"] == "DENEGADO"
        ]),
        "failed_mfa": len([
            event for event in events
            if event["reason"] == "MFA inválido"
        ]),
        "blocked_devices": len([
            device for device in devices
            if not device["authorized"]
        ])
    }

    return jsonify({
        "users": users,
        "devices": devices,
        "resources": resources,
        "policies": policies,
        "events": events,
        "stats": stats
    })


@app.post("/api/evaluate")
def evaluate():
    payload = request.get_json(force=True)
    return jsonify(evaluate_access(payload))


@app.post("/api/reset-events")
def reset_events():
    connection = get_connection()
    connection.execute("DELETE FROM audit_events")
    connection.commit()
    connection.close()

    return jsonify({"success": True})


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "mode": "laboratorio",
        "production_ready": False
    })


if __name__ == "__main__":
    initialize_database()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )