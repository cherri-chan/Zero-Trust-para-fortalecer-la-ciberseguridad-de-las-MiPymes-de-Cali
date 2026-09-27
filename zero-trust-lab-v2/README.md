# Laboratorio Zero Trust para MiPymes

## Descripción

Este proyecto es un prototipo funcional de laboratorio para demostrar principios de Zero Trust.

Su propósito es demostrar que una solicitud de acceso no debe depender únicamente de un usuario y una contraseña. El sistema evalúa:

- identidad;
- estado del usuario;
- MFA habilitado y resultado MFA;
- pertenencia del dispositivo al usuario;
- autorización del dispositivo;
- estado del dispositivo;
- postura;
- rol;
- recurso;
- segmento;
- política;
- decisión;
- auditoría.

## Correcciones incorporadas

Esta versión incorpora las siguientes correcciones respecto al MVP inicial:

1. El dispositivo debe pertenecer al usuario seleccionado.
2. `mfa_enabled` ahora forma parte de la decisión.
3. Las políticas se consultan desde SQLite mediante `rule_key`, `active` y `action`.
4. El sistema rechaza la solicitud cuando una política requerida está ausente, inactiva o no permite el acceso.
5. Los motivos de denegación conservan múltiples fallos cuando existen.
6. Las estadísticas históricas del dashboard se calculan directamente en la base de datos; los eventos mostrados siguen limitados a los 50 más recientes.
7. La API valida el JSON y los campos obligatorios.
8. El frontend escapa los valores antes de insertarlos en HTML.
9. Las pruebas automatizadas cubren asociación usuario-dispositivo, MFA, política inactiva, auditoría y otros casos adicionales.
10. SQLite activa `PRAGMA foreign_keys = ON` en cada conexión.

## Alcance académico

El sistema utiliza:

- Flask;
- SQLite;
- HTML;
- CSS;
- JavaScript;
- datos simulados;
- MFA simulado;
- segmentación lógica.

No representa una plataforma empresarial lista para producción.

## Estructura

```text
zero-trust-lab/
├── backend/
│   └── app.py
├── database/
│   ├── .gitkeep
│   └── zero_trust.db        # se crea automáticamente al ejecutar
├── diagrams/
│   └── architecture.mmd
├── documentation/
│   └── technical-notes.md
├── frontend/
│   └── templates/
│       └── index.html
├── tests/
│   └── test_policy.py
├── requirements.txt
└── README.md
```

## Requisitos

Python 3.10 o superior.

## Instalación

Desde la carpeta raíz:

```bash
python -m venv .venv
```

En Windows:

```bash
.venv\Scripts\activate
```

En Linux o macOS:

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Ejecución

Desde la carpeta raíz:

```bash
python backend/app.py
```

Abrir en el navegador:

```text
http://127.0.0.1:5000
```

La base de datos se crea automáticamente en:

```text
database/zero_trust.db
```

## Pruebas automatizadas

Ejecutar desde la raíz:

```bash
pytest -q
```

## Usuarios de demostración

| Usuario | Rol | Dispositivo |
|---|---|---|
| Carlos Pérez | Administrador | PC-ADM-001 |
| Ana Rodríguez | Operativo | PC-OP-002 |
| Usuario externo | Externo | MOV-EXT-003 |
| Cuenta suspendida | Operativo | PC-SUS-004 |

## Escenarios

### CP-01

Usuario operativo con MFA correcto, dispositivo autorizado y aplicación empresarial.

Resultado esperado:

```text
PERMITIDO
```

### CP-02

Usuario válido con MFA incorrecto.

Resultado esperado:

```text
DENEGADO
```

### CP-03

Usuario operativo solicita la base de datos protegida.

Resultado esperado:

```text
DENEGADO
```

### CP-04

Dispositivo externo bloqueado intenta acceder a la aplicación.

Resultado esperado:

```text
DENEGADO
```

### CP-05

Usuario con cuenta suspendida intenta solicitar acceso.

Resultado esperado:

```text
DENEGADO
```

### CP-06

Una solicitud evaluada aparece en el registro de auditoría.

### CP-07

La solicitud se origina desde un segmento diferente al segmento permitido.

Resultado esperado:

```text
DENEGADO
```

### CP-08

El dispositivo se encuentra bloqueado o revocado.

Resultado esperado:

```text
DENEGADO
```

## Limitaciones

- La identidad no utiliza un proveedor IAM real.
- El MFA es simulado.
- SQLite no ofrece alta disponibilidad.
- La segmentación es lógica.
- No existe integración con un SIEM.
- No existe revocación de sesión real.
- No se incluyen usuarios reales.
- No se ejecutan pruebas ofensivas.
- El sistema no garantiza la eliminación de incidentes.
- Los resultados del laboratorio no representan automáticamente a todas las MiPymes de Santiago de Cali.

## POWERED BY 🪴
