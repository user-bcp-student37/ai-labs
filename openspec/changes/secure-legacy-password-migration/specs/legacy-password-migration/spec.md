## ADDED Requirements

### Requirement: Clasificación de contraseñas almacenadas
El sistema SHALL tratar un valor almacenado en `legacy_users.password` como hash solo si cumple el formato de `PasswordHasher`; cualquier otro valor SHALL considerarse texto plano y migrarse.

#### Scenario: Texto plano con apariencia de prefijo BCrypt se migra
- **WHEN** existe un usuario cuyo `password` almacenado es `$2a$10$...` en texto plano y no cumple el formato de `PasswordHasher`
- **THEN** la migración SHALL reemplazar el valor almacenado por un hash válido
- **AND** el login con la contraseña original SHALL responder 200

#### Scenario: Valor con formato de hash malformado se trata como texto plano
- **WHEN** el `password` almacenado empieza con `$pbkdf2-sha256$` pero no cumple el formato completo
- **THEN** la migración SHALL reemplazar el valor por un hash válido

### Requirement: Hashes válidos no se recalculan
El sistema SHALL NOT modificar un `password` almacenado que ya cumple el formato de hash válido.

#### Scenario: Hash válido se preserva
- **WHEN** la migración se ejecuta sobre un usuario con hash válido
- **THEN** el valor almacenado SHALL permanecer igual

### Requirement: Migración idempotente
El sistema SHALL producir el mismo estado de `legacy_users` al ejecutar la migración una o varias veces.

#### Scenario: Re-ejecución no altera hashes migrados
- **GIVEN** un usuario con contraseña en texto plano ya migrada
- **WHEN** la migración se ejecuta de nuevo
- **THEN** el valor almacenado SHALL permanecer sin cambios

### Requirement: Fallo de inicialización visible en el arranque
El sistema SHALL propagar cualquier fallo de creación de directorio, conexión, creación de tabla, migración o seed de `LegacyDatabase.initialize()` como fallo de arranque, sin registrarlo y continuar.

#### Scenario: Base de datos no accesible impide el arranque
- **GIVEN** `AUTH_DB_URL` apunta a una ruta no accesible
- **WHEN** el servicio se inicia
- **THEN** el arranque SHALL fallar con un error observable
- **AND** el servicio SHALL NOT aceptar peticiones de `POST /auth/login`

#### Scenario: Fallo de migración impide el arranque
- **GIVEN** la migración de contraseñas lanza una excepción
- **WHEN** el servicio se inicia
- **THEN** el arranque SHALL fallar con un error observable

### Requirement: Contrato de login sin cambios
El sistema SHALL mantener el contrato de `POST /auth/login` documentado en `docs/ENDPOINTS.md` y las consultas parametrizadas de `LegacyDatabase`.

#### Scenario: Login con credenciales válidas tras migración
- **GIVEN** un usuario migrado desde texto plano
- **WHEN** envía sus credenciales originales a `POST /auth/login`
- **THEN** la respuesta SHALL ser 200 con los campos documentados

#### Scenario: Consultas parametrizadas
- **WHEN** se revisa `LegacyDatabase.findByCredentials` y la migración
- **THEN** las consultas SHALL usar parámetros enlazados y no concatenar entradas del usuario

### Requirement: Validación verificable
El cambio SHALL registrar su validación como ejecutada solo después de correr `python tools/lab.py test auth` con resultado observado.

#### Scenario: Validación pendiente
- **WHEN** el cambio se entrega sin ejecutar la suite
- **THEN** la validación SHALL figurar como **No ejecutado**
