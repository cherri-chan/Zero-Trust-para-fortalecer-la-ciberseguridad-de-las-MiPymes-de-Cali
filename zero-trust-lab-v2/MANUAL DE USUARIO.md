# Paso a paso para organizar y usar el laboratorio

## 1. Crear la carpeta principal

Crea una carpeta llamada:

```text
zero-trust-lab
```

## 2. Crear las subcarpetas

Dentro de ella crea exactamente:

```text
backend
frontend\templates
database
tests
diagrams
documentation
```

En Linux/macOS la ruta `frontend\templates` se interpreta como `frontend/templates`.

## 3. Copiar cada archivo en su ubicación

- `backend/app.py` → lógica del backend.
- `frontend/templates/index.html` → interfaz web.
- `tests/test_policy.py` → pruebas automatizadas.
- `requirements.txt` → dependencias.
- `README.md` → guía principal.
- `documentation/technical-notes.md` → notas técnicas.
- `diagrams/architecture.mmd` → diagrama Mermaid.
- `database/.gitkeep` → mantiene la carpeta en el proyecto.
- `.gitignore` → evita guardar el entorno virtual, cachés y la base de datos local.

No debes crear manualmente `database/zero_trust.db`. La aplicación la genera.

## 4. Abrir la terminal en la raíz

La terminal debe quedar ubicada donde están `README.md` y `requirements.txt`.

Comprueba que la estructura se vea así:

```text
zero-trust-lab/
├── backend/
├── database/
├── diagrams/
├── documentation/
├── frontend/
├── tests/
├── .gitignore
├── requirements.txt
└── README.md
```

## 5. Crear el entorno virtual

```bash
python -m venv .venv
```

## 6. Activarlo

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

## 7. Instalar dependencias

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 8. Ejecutar primero las pruebas

Desde la raíz:

```bash
pytest -q
```

Las pruebas verifican, entre otros casos, que un usuario no pueda utilizar el dispositivo de otra persona y que una política inactiva no permita el acceso.

## 9. Ejecutar el laboratorio

```bash
python backend/app.py
```

Deberá aparecer un servidor local en:

```text
http://127.0.0.1:5000
```

## 10. Abrir la interfaz

Abre el navegador e ingresa a:

```text
http://127.0.0.1:5000
```

## 11. Probar CP-01

1. Selecciona `Laboratorio Zero Trust`.
2. Carga `CP-01 Acceso válido`.
3. Presiona `Evaluar solicitud`.
4. Debes obtener `PERMITIDO`.
5. Verifica que aparezca un evento en `Auditoría`.

## 12. Probar CP-02

1. Carga `CP-02 MFA incorrecto`.
2. Evalúa la solicitud.
3. Debes obtener `DENEGADO`.
4. El motivo debe indicar `MFA inválido`.

## 13. Probar CP-03

1. Carga `CP-03 Permiso insuficiente`.
2. Evalúa.
3. Debes obtener `DENEGADO`.
4. El motivo debe indicar que el usuario no posee permisos para el recurso.

## 14. Probar CP-04

1. Carga `CP-04 Dispositivo bloqueado`.
2. Evalúa.
3. Debes obtener `DENEGADO`.
4. Debe aparecer el fallo del dispositivo.

## 15. Probar CP-05

1. Carga `CP-05 Usuario suspendido`.
2. Evalúa.
3. Debes obtener `DENEGADO`.

## 16. Probar CP-07

1. Carga `CP-07 Segmento incorrecto`.
2. Evalúa.
3. Debes obtener `DENEGADO`.
4. El motivo debe mencionar el segmento no autorizado.

## 17. Probar la corrección principal

1. Carga `Prueba extra: dispositivo ajeno`.
2. Evalúa.
3. Debes obtener `DENEGADO`.
4. El motivo debe indicar que el dispositivo no pertenece al usuario seleccionado.

Esta prueba es importante porque demuestra la corrección principal realizada al MVP.

## 18. Revisar la auditoría

Entra a `Auditoría`.

Verifica que cada ejecución haya generado un registro con:

- fecha;
- usuario;
- dispositivo;
- recurso;
- origen;
- resultado;
- motivo;
- política;
- severidad;
- tiempo de decisión.

## 19. Revisar las políticas

Entra a `Políticas`.

Debes encontrar `POL-01` a `POL-04` con su `rule_key`, prioridad, estado y acción.

## 20. Guardar evidencias para el informe

Para la sustentación, guarda capturas de:

1. CP-01 permitido.
2. CP-02 MFA denegado.
3. CP-03 permiso insuficiente.
4. CP-04 dispositivo bloqueado.
5. Prueba extra de dispositivo ajeno.
6. Tabla de auditoría.
7. Tabla de políticas.
8. Dashboard con los indicadores.

## 21. Qué archivos entregar

Para una entrega académica puedes conservar:

```text
zero-trust-lab/
├── backend/app.py
├── frontend/templates/index.html
├── tests/test_policy.py
├── diagrams/architecture.mmd
├── documentation/technical-notes.md
├── requirements.txt
├── README.md
└── .gitignore
```

No es necesario adjuntar `.venv/`.

La base de datos `database/zero_trust.db` puede omitirse si la entrega debe quedar reproducible desde cero, porque se genera automáticamente.

## 22. Recomendación para la presentación

Durante la sustentación, explica que las políticas están almacenadas y parametrizadas en SQLite, pero que la interpretación de cada `rule_key` todavía reside en el código. Eso evita presentar el sistema como un motor empresarial completamente independiente del código.

También aclara que MFA, identidad y segmentación son simulados y que el sistema está diseñado para ejecutarse únicamente en `127.0.0.1`.
