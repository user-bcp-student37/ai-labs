# Tasks

Unidad de trabajo: Issue #22 (H-AUTH-01). Todas las pruebas se ejecutan desde `auth/`.

## 1. Pruebas de caracterización (sin cambiar comportamiento)

- [x] 1.1 Ejecutar `mvn test` en `auth/` sobre el código sin modificar y verificar que `logsInWithWorkshopUser` (`student` / `Workshop123!` -> 200, `user.username`, `token`) pasa.
- [x] 1.2 En `AuthResourceTest`, agregar pruebas que fijen la validación actual (usuario ausente -> 400, contraseña ausente -> 400) y verificar que pasan sobre el código sin modificar.
- [x] 1.3 En `AuthResourceTest`, agregar una prueba de credenciales inválidas comunes (`student` con contraseña incorrecta -> 401 sin `token`) y verificar que pasa sobre el código sin modificar.

## 2. Pruebas de regresión del Issue (rojas antes de la corrección)

- [x] 2.1 En `AuthResourceTest`, agregar una prueba con `' OR '1'='1` como usuario y `Workshop123!` como contraseña que espere 401 sin `token`; verificar que falla (200) sobre el código sin corregir.
- [x] 2.2 En `AuthResourceTest`, agregar una prueba con `student` como usuario y `' OR '1'='1` como contraseña que espere 401 sin `token`; verificar que falla (200) sobre el código sin corregir.
- [x] 2.3 Ejecutar `mvn test` en `auth/` y verificar que solo fallan las dos pruebas de la sección 2 y que pasan todas las de la sección 1.

## 3. Corrección incremental

- [x] 3.1 En `LegacyDatabase.findByCredentials`, reemplazar la consulta concatenada por una consulta parametrizada (`PreparedStatement`) con `username` y `password` como parámetros, conservando columnas, coincidencia exacta, mapeo a `UserRecord` y manejo de excepciones; verificar con búsqueda de texto que ninguna consulta concatena esos valores.
- [x] 3.2 Ejecutar `mvn test` en `auth/` y verificar que pasan todas las pruebas, incluidas las dos de inyección y el login válido (200 con `user.username` y `token`).

## 4. Validación final

- [x] 4.1 Ejecutar `mvn verify` en `auth/` y verificar en el reporte JaCoCo que las líneas modificadas de `findByCredentials` están cubiertas (meta: 85% o más).
- [x] 4.2 Revisar `git diff --stat` y verificar que solo cambian `LegacyDatabase.java`, `AuthResourceTest.java` y los artefactos de este cambio OpenSpec, sin cambios en `api/`, `web/` ni `docs/`.
- [x] 4.3 Ejecutar `openspec validate "h-auth-01-parametrized-login-credentials"` desde la raíz y verificar que el cambio sigue siendo válido.

## Workflow follow-up

- Solicitar revisión humana antes de integrar.
- Archivar el cambio cuando se cumplan los requisitos de revisión del proyecto.
