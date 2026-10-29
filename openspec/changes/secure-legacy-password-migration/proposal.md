## Por qué

El Issue #24 (HU-01 "Migrar contraseñas legacy de forma segura", hallazgo H-AUTH-02, fuente de alcance `HU-01.md`) identifica dos riesgos en `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`:

- La migración de contraseñas en texto plano depende de la detección de formato. Una contraseña en texto plano que tenga apariencia de hash no debe quedar sin migrar.
- `initialize()` captura cualquier `Exception` y solo ejecuta `printStackTrace()`. Un fallo de creación del directorio, de conexión, de creación de tabla, de migración o de seed deja la aplicación arrancando como si la base estuviera lista.

## Qué cambia

- Hacer explícito y verificable el criterio que distingue un hash válido de una contraseña en texto plano, sin depender solo de un prefijo.
- Agregar pruebas de regresión: una contraseña en texto plano que empieza con un prefijo de hash (por ejemplo `$2a$`) se migra, cambia su valor almacenado y la contraseña original sigue autenticando.
- Verificar la idempotencia: volver a ejecutar la migración no modifica un hash ya migrado.
- Hacer que un fallo de inicialización o de migración se propague al arranque en lugar de registrarse y continuar.
- Agregar pruebas de los caminos de fallo de inicialización, sin afirmar resultados que no se hayan ejecutado.

Capacidad afectada: `legacy-password-migration` (nueva, ver `specs/legacy-password-migration/spec.md`).

## Alcance

Dentro del alcance:

- Clasificación de valores almacenados en `legacy_users` (hash válido frente a texto plano).
- Propagación de errores de `LegacyDatabase.initialize()` al arranque del servicio.
- Pruebas de regresión e idempotencia de la migración y de los caminos de fallo.

Fuera del alcance:

- Cambiar el formato del token (`LegacyTokenUtil`) o su secreto.
- Cambiar el contrato de `POST /auth/login` documentado en `docs/ENDPOINTS.md`.
- Cambiar las cuentas semilla `student` y `trainer`.
- Refactorizar más allá de lo necesario para el alcance (separación en capas de `AuthResource` queda para otro cambio).
- Diseño técnico detallado y lista de tareas: este cambio no incluye `design.md` ni `tasks.md` por instrucción explícita.

## Comportamiento que se conserva

- `POST /auth/login` mantiene su contrato, incluidos los códigos de respuesta y los campos de respuesta documentados en `docs/ENDPOINTS.md`.
- Las consultas SQL siguen parametrizadas.
- `GET /q/health` sigue respondiendo 200 cuando el servicio está operativo.
- Los observables del login que documenta `docs/ENDPOINTS.md` (incluido `expiresIn` de 3600 y el campo `debug`) no cambian.
- Las observaciones de `docs/ENDPOINTS.md` sobre el 401 (que refleja el nombre de usuario) y el 500 (que expone la clase de excepción) no se modifican en este cambio, salvo que se decida lo contrario de forma explícita.

## Puntos abiertos y discrepancias

- HU-01 y el Issue mencionan hashes BCrypt y los prefijos `$2a$`, `$2b$`, `$2y$`. El código actual usa `PasswordHasher` con formato PBKDF2 (`$pbkdf2-sha256$...`) y comprueba el formato completo mediante `isEncoded`, no solo un prefijo. El criterio de este cambio debe confirmarse con el equipo antes de implementar.
- Las líneas de evidencia citadas en HU-01 (25-30 y 67-92) no coinciden con el archivo actual. El hallazgo debe revalidarse contra el código vigente.
- El cuerpo del Issue #24 no se pudo recuperar mediante el MCP de GitHub; el alcance se tomó de `HU-01.md`.
- Estado de validación: **No ejecutado**. Debe ejecutarse `python tools/lab.py test auth` antes de cerrar el cambio.
