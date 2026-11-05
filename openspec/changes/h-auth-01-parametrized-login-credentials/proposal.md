# Proposal

## Why

El Issue #22 (H-AUTH-01, severidad alta) reporta que el login puede aceptar credenciales manipuladas con sintaxis SQL, lo que permite autenticarse sin conocer la contraseña. Corregir el comportamiento evita el bypass y conserva el acceso de usuarios con credenciales válidas.

## What Changes

- Para `POST /auth/login`, las credenciales que intentan alterar la consulta de autenticación se rechazan como credenciales inválidas: respuesta 401 y sin token.
- El login con las credenciales válidas de workshop conserva la respuesta exitosa observable: 200, `user.username` y `token`.
- El contrato de `docs/ENDPOINTS.md` no contiene una sección de `auth` ni documenta `/auth/login`; por ello, no se atribuyen a ese documento requisitos de login que no establece. El escenario de éxito preserva el comportamiento actualmente comprobado por `AuthResourceTest`; los escenarios de rechazo concretan el cambio pedido por el Issue.

## Capabilities

### New Capabilities

- `auth-login`: comportamiento observable del inicio de sesión y validación de credenciales.

### Modified Capabilities

- Ninguna. El repositorio no tiene specs existentes.

## Impact

- Alcance: componente `auth/`, endpoint `POST /auth/login` y sus pruebas.
- Fuera de alcance: componentes `api/` y `web/`, el formato o ciclo de vida del token y otros contratos ajenos a la validación de credenciales.
- No se cambia el contrato documentado de `api/` ni se modifican documentos generales.
