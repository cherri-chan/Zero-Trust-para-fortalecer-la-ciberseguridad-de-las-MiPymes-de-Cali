# Notas técnicas del laboratorio

## Naturaleza del proyecto

El sistema es un prototipo funcional de laboratorio para demostrar principios de Zero Trust.

No es una plataforma empresarial productiva y no debe conectarse a sistemas reales.

## Flujo de evaluación

1. Buscar el usuario.
2. Verificar que la cuenta esté activa.
3. Verificar que MFA esté habilitado.
4. Validar el resultado simulado de MFA.
5. Buscar el dispositivo.
6. Verificar que el dispositivo pertenezca al usuario.
7. Comprobar autorización, estado y postura del dispositivo.
8. Validar el rol frente al recurso.
9. Validar el segmento lógico.
10. Verificar que las políticas requeridas estén activas y configuradas para permitir.
11. Tomar la decisión con criterio de rechazo por defecto.
12. Registrar el evento.
13. Mostrar el resultado en el panel.

## Políticas

Las cuatro políticas principales se almacenan en SQLite y tienen un `rule_key` que relaciona el registro persistido con la condición evaluada por el motor:

- `identity_mfa`: identidad activa y MFA válido.
- `device`: dispositivo asociado, autorizado, activo y conforme.
- `role_resource`: rol compatible con el recurso.
- `segment`: segmento de origen compatible con el recurso.

Una política ausente, inactiva o distinta de `PERMITIR` hace que la solicitud se deniegue.

## Recursos protegidos

- Aplicación empresarial.
- Servidor de archivos.
- Base de datos protegida.

## Roles

### Administrador

Tiene acceso a todos los recursos definidos en el laboratorio, siempre que las demás condiciones se cumplan.

### Operativo

Puede acceder a recursos cuyo `required_role` sea `Operativo`.

### Externo

Se utiliza para demostrar el bloqueo de un dispositivo no autorizado.

## MFA

El segundo factor se simula mediante los valores:

- `correcto`
- `incorrecto`

Además, el usuario debe tener `mfa_enabled = 1`.

No se utiliza un proveedor MFA externo real.

## Segmentación

La segmentación se representa mediante los valores:

- `SEG-01`: usuarios.
- `SEG-02`: administración.
- `SEG-03`: recursos protegidos.

No se crean VLAN ni reglas físicas de firewall.

## Seguridad

El laboratorio debe ejecutarse únicamente con datos ficticios en `127.0.0.1`.

No deben realizarse pruebas contra sistemas productivos, direcciones externas o infraestructuras de terceros.

## Limitaciones

- La identidad no utiliza un proveedor IAM real.
- MFA es simulado.
- La segmentación es lógica.
- SQLite se utiliza exclusivamente para el laboratorio.
- No existe SIEM.
- No existe revocación de sesión real; CP-08 se interpreta como dispositivo bloqueado o revocado.
- La tabla de políticas es parametrizable a nivel de activación, acción y regla, pero la semántica de cada `rule_key` continúa implementada en código.
