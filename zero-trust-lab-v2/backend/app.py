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
    template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    mfa_enabled INTEGER NOT NULL CHECK (mfa_enabled IN (0, 1))
);

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY,
    identifier TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    operating_system TEXT NOT NULL,
    status TEXT NOT NULL,
    authorized INTEGER NOT NULL CHECK (authorized IN (0, 1)),
    posture TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    resource_type TEXT NOT NULL,
    segment TEXT NOT NULL,
    sensitivity TEXT NOT NULL,
    required_role TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    rule_key TEXT NOT NULL UNIQUE,
    priority INTEGER NOT NULL,
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
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


SEED_USERS = [
    (1, "Carlos Pérez", "carlos@empresa.local", "Administrador", 1, 1),
    (2, "Ana Rodríguez", "ana@empresa.local", "Operativo", 1, 1),
    (3, "Usuario externo", "externo@empresa.local", "Externo", 1, 1),
    (4, "Cuenta suspendida", "suspendida@empresa.local", "Operativo", 0, 1),
]

SEED_DEVICES = [
    (1, "PC-ADM-001", 1, "Portátil", "Windows", "Activo", 1, "Conforme"),
    (2, "PC-OP-002", 2, "Escritorio", "Linux", "Activo", 1, "Conforme"),
    (3, "MOV-EXT-003", 3, "Móvil", "Android", "Bloqueado", 0, "No conforme"),
    (4, "PC-SUS-004", 4, "Portátil", "Windows", "Activo", 1, "Conforme"),
]

SEED_RESOURCES = [
    (1, "Aplicación empresarial", "Aplicación", "SEG-03", "Media", "Operativo"),
    (2, "Servidor de archivos", "Archivos", "SEG-03", "Alta", "Operativo"),
    (3, "Base de datos protegida", "Base de datos", "SEG-03", "Crítica", "Administrador"),
]

SEED_POLICIES = [
    (1, "POL-01", "Identidad y MFA válidos", "identity_mfa", 1, 1, "PERMITIR"),
    (2, "POL-02", "Dispositivo autorizado y conforme", "device", 2, 1, "PERMITIR"),
    (3, "POL-03", "Rol compatible con el recurso", "role_resource", 3, 1, "PERMITIR"),
    (4, "POL-04", "Segmento autorizado", "segment", 4, 1, "PERMITIR"),
]


def get_connection():
    os.makedirs(DATABASE_DIR, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    connection = get_connection()

    # Compatibilidad con la base de datos del MVP anterior:
    # si no existe `rule_key`, se reconstruye la base de datos porque
    # todos los datos del laboratorio son simulados.
    table_exists = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'policies'"
    ).fetchone()
    if table_exists:
        policy_columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(policies)").fetchall()
        }
        if "rule_key" not in policy_columns:
            connection.executescript(
                """
                DROP TABLE IF EXISTS audit_events;
                DROP TABLE IF EXISTS policies;
                DROP TABLE IF EXISTS resources;
                DROP TABLE IF EXISTS devices;
                DROP TABLE IF EXISTS users;
                """
            )

    connection.executescript(SCHEMA)

    existing_users = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if existing_users == 0:
        connection.executemany(
            """
            INSERT INTO users (id, name, email, role, active, mfa_enabled)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            SEED_USERS,
        )

        connection.executemany(
            """
            INSERT INTO devices (
                id, identifier, user_id, type, operating_system,
                status, authorized, posture
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            SEED_DEVICES,
        )

        connection.executemany(
            """
            INSERT INTO resources (
                id, name, resource_type, segment, sensitivity, required_role
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            SEED_RESOURCES,
        )

        connection.executemany(
            """
            INSERT INTO policies (
                id, code, name, rule_key, priority, active, action
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            SEED_POLICIES,
        )

    connection.commit()
    connection.close()


def query_rows(sql, parameters=()):
    connection = get_connection()
    rows = [dict(row) for row in connection.execute(sql, parameters).fetchall()]
    connection.close()
    return rows


def load_policies(connection):
    rows = connection.execute(
        "SELECT * FROM policies ORDER BY priority"
    ).fetchall()
    return {row["rule_key"]: row for row in rows}


def policy_ready(policy):
    return (
        policy is not None
        and bool(policy["active"])
        and policy["action"] == "PERMITIR"
    )


def evaluate_access(payload, save_event=True):
    start_time = time.perf_counter()
    payload = payload or {}

    connection = get_connection()
    policies = load_policies(connection)

    user = connection.execute(
        "SELECT * FROM users WHERE id = ?",
        (payload.get("user_id"),),
    ).fetchone()

    device = connection.execute(
        "SELECT * FROM devices WHERE id = ?",
        (payload.get("device_id"),),
    ).fetchone()

    resource = connection.execute(
        "SELECT * FROM resources WHERE id = ?",
        (payload.get("resource_id"),),
    ).fetchone()

    checks = []
    failures = []
    applied_policies = []

    def apply_check(name, ok, reason=None, policy_key=None):
        policy_ok = True
        if policy_key:
            policy = policies.get(policy_key)
            policy_ok = policy_ready(policy)
            if policy_ok:
                applied_policies.append(policy["code"])
            else:
                policy_code = policy["code"] if policy else policy_key
                failures.append(
                    f"La política {policy_code} no está activa o no permite el acceso"
                )

        final_ok = bool(ok) and policy_ok
        checks.append((name, final_ok))

        if not final_ok and reason:
            failures.append(reason)
        return final_ok

    identity_ok = user is not None and bool(user["active"])
    apply_check(
        "Identidad",
        identity_ok,
        "Identidad no encontrada" if user is None else "Usuario suspendido",
        "identity_mfa",
    )

    mfa_valid = (
        user is not None
        and bool(user["mfa_enabled"])
        and payload.get("mfa") == "correcto"
    )
    apply_check(
        "MFA",
        mfa_valid,
        (
            "MFA no habilitado para el usuario"
            if user is not None and not user["mfa_enabled"]
            else "MFA inválido"
        ),
        "identity_mfa",
    )

    device_belongs_to_user = (
        user is not None
        and device is not None
        and device["user_id"] == user["id"]
    )
    device_valid = (
        device_belongs_to_user
        and bool(device["authorized"])
        and device["status"] == "Activo"
        and device["posture"] == "Conforme"
    )

    if device is None:
        device_reason = "Dispositivo no encontrado"
    elif not device_belongs_to_user:
        device_reason = "El dispositivo no pertenece al usuario seleccionado"
    elif not device_valid:
        device_reason = "Dispositivo no autorizado o postura no conforme"
    else:
        device_reason = None

    apply_check("Dispositivo", device_valid, device_reason, "device")

    role_valid = (
        user is not None
        and resource is not None
        and bool(user["active"])
        and user["role"] == resource["required_role"]
    )
    if user is not None and user["role"] == "Administrador":
        role_valid = resource is not None and bool(user["active"])

    if resource is None:
        role_reason = "Recurso no encontrado"
    elif not role_valid:
        role_reason = "El usuario no posee permisos para el recurso"
    else:
        role_reason = None

    apply_check("Rol", role_valid, role_reason, "role_resource")

    segment_valid = (
        resource is not None
        and payload.get("segment") == resource["segment"]
    )
    segment_reason = None if segment_valid else "Segmento de red no autorizado"
    apply_check("Política/segmento", segment_valid, segment_reason, "segment")

    all_checks_ok = all(status for _, status in checks)
    result = "PERMITIDO" if all_checks_ok and not failures else "DENEGADO"

    if result == "PERMITIDO":
        reason = "Todas las condiciones fueron verificadas"
        severity = "Baja"
    else:
        # Preserva el orden y elimina repeticiones para que la auditoría sea legible.
        unique_failures = list(dict.fromkeys(failures))
        reason = "; ".join(unique_failures) or "Solicitud rechazada por política"
        severity = "Alta"

    decision_time = round((time.perf_counter() - start_time) * 1000, 3)

    policy_text = " + ".join(dict.fromkeys(applied_policies)) or "Ninguna"

    event = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "user_name": user["name"] if user else "Desconocido",
        "device_name": device["identifier"] if device else "Desconocido",
        "resource_name": resource["name"] if resource else "Desconocido",
        "origin": str(payload.get("origin", "SEG-01")),
        "result": result,
        "reason": reason,
        "policy": policy_text,
        "severity": severity,
        "decision_ms": decision_time,
    }

    if save_event:
        connection.execute(
            """
            INSERT INTO audit_events (
                timestamp, user_name, device_name, resource_name,
                origin, result, reason, policy, severity, decision_ms
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
                event["decision_ms"],
            ),
        )
        connection.commit()

    connection.close()

    return {
        "result": result,
        "reason": reason,
        "policy": policy_text,
        "severity": severity,
        "decision_ms": decision_time,
        "checks": [
            {"name": name, "ok": status}
            for name, status in checks
        ],
        "event": event,
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/api/data")
def get_data():
    initialize_database()

    users = query_rows("SELECT * FROM users ORDER BY id")

    devices = query_rows(
        """
        SELECT devices.*, users.name AS user_name
        FROM devices
        LEFT JOIN users ON users.id = devices.user_id
        ORDER BY devices.id
        """
    )

    resources = query_rows("SELECT * FROM resources ORDER BY id")
    policies = query_rows("SELECT * FROM policies ORDER BY priority")
    events = query_rows(
        """
        SELECT * FROM audit_events
        ORDER BY id DESC
        LIMIT 50
        """
    )

    connection = get_connection()
    stats = {
        "active_users": connection.execute(
            "SELECT COUNT(*) FROM users WHERE active = 1"
        ).fetchone()[0],
        "authorized_devices": connection.execute(
            "SELECT COUNT(*) FROM devices WHERE authorized = 1"
        ).fetchone()[0],
        "allowed_requests": connection.execute(
            "SELECT COUNT(*) FROM audit_events WHERE result = 'PERMITIDO'"
        ).fetchone()[0],
        "denied_requests": connection.execute(
            "SELECT COUNT(*) FROM audit_events WHERE result = 'DENEGADO'"
        ).fetchone()[0],
        "failed_mfa": connection.execute(
            "SELECT COUNT(*) FROM audit_events WHERE reason LIKE '%MFA%'"
        ).fetchone()[0],
        "blocked_devices": connection.execute(
            "SELECT COUNT(*) FROM devices WHERE authorized = 0"
        ).fetchone()[0],
    }
    connection.close()

    return jsonify({
        "users": users,
        "devices": devices,
        "resources": resources,
        "policies": policies,
        "events": events,
        "stats": stats,
    })


@app.post("/api/evaluate")
def evaluate():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "El cuerpo de la solicitud debe ser JSON."}), 400

    required_fields = ("user_id", "device_id", "resource_id", "mfa", "segment")
    missing = [field for field in required_fields if field not in payload]
    if missing:
        return jsonify({
            "error": "Faltan campos obligatorios.",
            "missing": missing,
        }), 400

    try:
        result = evaluate_access(payload)
    except (sqlite3.Error, ValueError, TypeError) as exc:
        return jsonify({"error": f"No fue posible evaluar la solicitud: {exc}"}), 500

    return jsonify(result)


@app.post("/api/reset-events")
def reset_events():
    connection = get_connection()
    connection.execute("DELETE FROM audit_events")
    connection.commit()
    connection.close()
    return jsonify({"success": True})


@app.get("/health")
def health():
    initialize_database()
    return jsonify({
        "status": "ok",
        "mode": "laboratorio",
        "production_ready": False,
    })


# El laboratorio solo se ejecuta sobre loopback por diseño académico.
if __name__ == "__main__":
    initialize_database()
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
