# Notas técnicas del laboratorio

## Naturaleza del proyecto

El sistema es un prototipo funcional de laboratorio para demostrar principios de Zero Trust.

No es una plataforma empresarial productiva y no debe conectarse a sistemas reales.

## Flujo de evaluación

1. Buscar el usuario.
2. Verificar que la cuenta esté activa.
3. Validar MFA.
4. Verificar el dispositivo.
5. Comprobar autorización y postura.
6. Validar el rol frente al recurso.
7. Validar el segmento lógico.
8. Tomar la decisión.
9. Registrar el evento.
10. Mostrar el resultado en el panel.

## Recursos protegidos

- Aplicación empresarial.
- Servidor de archivos.
- Base de datos protegida.

## Roles

### Administrador

Tiene acceso a todos los recursos definidos en el laboratorio.

### Operativo

Puede acceder a la aplicación empresarial y al servidor de archivos.

### Externo

Se utiliza para demostrar el bloqueo de un dispositivo no autorizado.

## MFA

El segundo factor se simula mediante los valores:

- `correcto`
- `incorrecto`

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