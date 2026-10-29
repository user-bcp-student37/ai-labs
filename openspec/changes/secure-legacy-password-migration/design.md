## Contexto técnico

- Componente: `auth/` (Java 21 / Quarkus, SQLite vía JDBC, Maven).
- `LegacyDatabase` (`@ApplicationScoped`) crea `legacy_users`, migra contraseñas en texto plano con `migratePlaintextPasswords`, siembra `student` y `trainer` con `seedUserIfMissing` y autentica con `findByCredentials`.
- `PasswordHasher` define el formato de hash propio `$pbkdf2-sha256$600000$<salt>$<key>` (base64 URL sin padding, salt 16 bytes, clave 256 bits). `isEncoded` y `matches` usan el mismo `parse`, que valida formato completo, no solo prefijo.
- Con esto, un valor `$2a$10$...` en texto plano ya no se toma como hash: `isEncoded` devuelve false y se migra. La brecha real de H-AUTH-02 es `initialize()`, que captura `Exception` y solo hace `printStackTrace()`.
- `DB_URL` es `static final` y se lee del entorno al cargar la clase, por lo que cada prueba no puede cambiarla por sí sola.
- Pruebas existentes relevantes en `AuthResourceTest`: `storesSeedPasswordAsHash`, `migratesExistingPlaintextPasswordsIdempotently` (usa `LegacyFixture123!`, sin prefijo), `seedsMissingUserWithHashedPassword`, y el 500 que mockea `LegacyDatabase`.

## Goals

- Mantener la detección actual basada en el formato completo de `PasswordHasher` y dejarla cubierta por pruebas de regresión con prefijos tipo `$2a$`, `$2b$`, `$2y$` y `$pbkdf2-sha256$` malformado.
- Hacer que un fallo de `initialize()` (directorio, conexión, DDL, migración, seed) impida el arranque, sin registrar y continuar.
- Conservar idempotencia de la migración y el contrato de `POST /auth/login`.

## Non-goals

- No cambiar el formato de hash, la constante de iteraciones ni `PasswordHasher`.
- No cambiar `LegacyTokenUtil`, el secreto del token ni las cuentas semilla.
- No introducir columna de marcador de migración ni migración de esquema.
- No separar `AuthResource` en capas ni refactorizar más allá de `LegacyDatabase`.
- No cambiar las observaciones de `docs/ENDPOINTS.md` sobre 401 y 500.

## Contratos protegidos

- `POST /auth/login`: códigos 200, 400 (`Request is null`, `Username is required`, `Password is required`), 401 (`Invalid user <u> or password`), 405, 406, 415 y 500; campos `token`, `expiresIn` = 3600, `user` (`username`, `displayName` escapado, `role`) y `debug` = `authenticated-with-legacy-flow`.
- `GET /q/health` responde 200 con el servicio operativo.
- Esquema `legacy_users(id, username, password, display_name, role)` sin cambios.
- Consultas SQL parametrizadas (`findByCredentials`, `UPDATE ... WHERE id = ?`, `INSERT OR IGNORE`).

## Componentes afectados

- `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`: `initialize()`, posiblemente `migratePlaintextPasswords` si se decide reforzar la detección.
- `auth/src/main/java/com/bcp/workshop/auth/PasswordHasher.java`: solo lectura; `isEncoded` es la fuente de la clasificación.
- `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` y/o nuevas clases de prueba bajo el mismo paquete para caracterización y fallos de arranque.
- Sin cambios en `AuthResource`, `LegacyTokenUtil` ni en `web/` o `api/`.

## Decisiones técnicas y alternativas

1. Clasificación de texto plano: mantener `PasswordHasher.isEncoded` (validación de formato completo) como criterio. Alternativas descartadas: (a) prefijo `$2a$` o similar, que confunde formatos ajenos y no valida la estructura; (b) columna `migrated` o `hash_version`, que implica cambio de esquema fuera de alcance. Trade-off: una contraseña en texto plano con formato PBKDF2 válido exacto seguiría sin migrarse; es improbable y se documenta como riesgo residual.
2. Propagación de fallos: `initialize()` deja de capturar `Exception` y propaga una excepción no comprobada (por ejemplo `IllegalStateException` con causa) para que el arranque falle. Alternativa: capturar y marcar un estado "no listo" que responda 500 en login; se descarta porque el alcance pide fallo observable en el arranque y evita servir peticiones con base no inicializada.
3. Momento de ejecución: `@PostConstruct` en un bean `@ApplicationScoped` se ejecuta de forma perezosa en el primer uso, no en el arranque. Para que el fallo sea de arranque hay que forzar la inicialización eager, por ejemplo con la anotación `@Startup` de Quarkus o un observador de `StartupEvent`. Esta suposición debe validarse con la prueba de caracterización antes de cambiar nada.
4. Pruebas de fallo de arranque: `DB_URL` es estático y se lee al cargar la clase. Las pruebas de fallo deben ejecutarse en un proceso o perfil separado con `AUTH_DB_URL` apuntando a una ruta no accesible, o validarse llamando a `initialize()` directamente con un `Connection` o URL inválida en pruebas unitarias sin Quarkus. Alternativa descartada: mutar `DB_URL` por reflexión, frágil.

## Estrategia incremental

1. Caracterizar el comportamiento actual sin tocar producción: login 200/400/401, migración de `LegacyFixture123!`, idempotencia, seed con hash.
2. Agregar pruebas de regresión: texto plano con prefijo `$2a$10$...` migra y autentica; `$pbkdf2-sha256$` malformado migra; hash válido no cambia.
3. Caracterizar el arranque actual: confirmar que un fallo de `initialize()` hoy no detiene nada y que la inicialización ocurre en el primer uso. Registrar la evidencia observada.
4. Cambiar `initialize()` para propagar excepciones y, si la evidencia del paso 3 lo confirma, activar la inicialización eager (`@Startup` o `StartupEvent`).
5. Agregar pruebas de fallo de arranque en proceso o perfil separado.
6. Ejecutar `python tools/lab.py test auth` y registrar resultados reales; meta de cobertura del código modificado 85% o más.

Cada paso se revisa como PR pequeño y el paso 4 no se integra sin los pasos 1 a 3 en verde.

## Pruebas de caracterización necesarias antes de modificar

- Login válido de `student` y `trainer` (200, campos completos, `expiresIn` 3600, `debug`).
- Login con credenciales incorrectas (401 con el mensaje actual) y usuario inexistente.
- Validaciones 400, 405, 406 y 415 sin cambios.
- Migración de `LegacyFixture123!` y segunda ejecución sin cambio del valor almacenado.
- `seedUserIfMissing` no duplica usuarios y guarda hash.
- Comportamiento actual de un fallo de `initialize()`: debe quedar documentado como línea base, no como resultado deseado.

## Riesgos y trade-offs

- Arranque perezoso: si la inicialización eager no se activa, el fallo seguirá apareciendo en la primera petición. Riesgo alto para el criterio de arranque; mitigado por el paso 3.
- Falsos negativos de migración en texto plano con formato PBKDF2 exacto: riesgo bajo, residual, documentado.
- Cambiar a propagación puede dejar la app sin arrancar en entornos con `AUTH_DB_URL` mal configurado; es el comportamiento deseado, pero debe documentarse en la guía de ejecución.
- Pruebas de fallo de arranque más lentas y dependientes de proceso separado.
- Discrepancia BCrypt frente a PBKDF2 y líneas de HU-01 desactualizadas siguen pendientes de confirmación del equipo.

## Rollback

- Cada paso es un commit o PR independiente. Revertir el paso 4 devuelve `initialize()` a capturar y registrar; las pruebas de caracterización y de regresión se mantienen.
- No hay migración de datos irreversible: los hashes ya generados son compatibles con el código anterior, porque el formato no cambia.
- Si se activó `@Startup` y causa fallos en otros entornos, retirar la anotación restaura el arranque perezoso sin tocar datos.
