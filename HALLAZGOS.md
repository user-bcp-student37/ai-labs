# Hallazgos

## auth

Discovery inicial estático del flujo de login. `docs/ENDPOINTS.md` no existe,
por lo que el contrato indicado abajo es el observado en código, no un contrato
acordado. Después, H-AUTH-01 y H-AUTH-03 se corrigieron y verificaron con
`mvn verify` desde `auth/` usando JDK 21 (9 pruebas aprobadas). No se consultaron
advisories de dependencias; CodeQL y Dependency Review remotos no se ejecutaron.

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-AUTH-01 | auth | SQL: concatenación de credenciales | Vulnerabilidad | Resuelto: `findByCredentials` usa `PreparedStatement` y parámetros para usuario y contraseña; prueba de regresión confirma login literal con nombre que contiene comilla. | auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:35; auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:84-98; auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:67-82 | alta | Resuelto |
| H-AUTH-02 | auth | Token: Base64 con secreto embebido | Vulnerabilidad | El contenido Base64 no constituye una firma; el token incluye usuario, rol, expiración y un secreto compilado en el código. Quien conozca el formato puede leer el contenido y el token no demuestra integridad criptográfica. | auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:39-42; auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:8,12-15 | alta | Pendiente |
| H-AUTH-03 | auth | Datos: contraseñas almacenadas en texto plano | Vulnerabilidad | Resuelto: PBKDF2-HMAC-SHA256 con salt aleatorio y migración idempotente de credenciales plaintext existentes; conserva el login con las contraseñas actuales. | auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:26-33,40-81,84-94; auth/src/main/java/com/bcp/workshop/auth/PasswordHasher.java:15-107; auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:85-134; auth/src/test/java/com/bcp/workshop/auth/PasswordHasherTest.java:11-35 | alta | Resuelto |
| H-AUTH-04 | auth | Configuración: origen CORS demasiado amplio | Vulnerabilidad | CORS acepta cualquier origen mediante una expresión general. Esto amplía los sitios que pueden intentar leer respuestas desde navegadores de usuarios; el impacto concreto depende de los controles de autenticación y de los datos expuestos. | auth/src/main/resources/application.properties:4-7 | media | Pendiente |
| H-AUTH-05 | auth | Errores: respuesta expone detalles internos | Vulnerabilidad | El recurso devuelve el mensaje de excepción y el nombre de su clase al cliente. La base también imprime excepciones completas en el log; los detalles pueden revelar información de implementación y dificultar el control de los mensajes. | auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:54-58; auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:35-36,95-96 | media | Pendiente |
| H-AUTH-06 | auth | SCA: dependencias candidatas a revisión de advisories | Sugerencia | El POM declara Quarkus 3.27.4 y Commons Text 1.9, como indica el reto. La presencia de esas versiones está comprobada, pero no se verificó si tienen advisories aplicables; no se afirma aquí una CVE ni vulnerabilidad concreta. | auth/pom.xml:13,49-50 | media | Pendiente |
| H-AUTH-07 | auth | Clean code: recurso mezcla validación, persistencia, token y respuesta | Refactor | `login` valida la solicitud, consulta la base, genera el token y arma la respuesta en un mismo método; los cambios o errores en una responsabilidad quedan acoplados a las demás y son más difíciles de probar aisladamente. | auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:24-49 | baja | Pendiente |

### Contrato de login observado en código

- Ruta: `POST /auth/login`, consume y produce JSON. El DTO declara `username`,
  `password` y `client`; `client` no se usa en el recurso.
  Evidencia: `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:15-24`,
  `auth/src/main/java/com/bcp/workshop/auth/LoginRequest.java:3-7`.
- Validación: solicitud nula, usuario vacío/nulo o contraseña vacía/nula
  responden `400` con un objeto JSON que contiene `message`.
  Evidencia: `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:26-33`.
- Credenciales que no encuentran usuario responden `401`; las válidas responden
  `200` con `token`, `expiresIn`, `user` (`username`, `displayName`, `role`) y
  `debug`. Una excepción capturada por el recurso responde `500` con `message`
  y `exception`.
  Evidencia: `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:35-58`.
- La persistencia usa SQLite con `AUTH_DB_URL` o `jdbc:sqlite:./data/workshop.db`
  por defecto, migra contraseñas plaintext existentes y crea hashes para las
  cuentas ficticias al inicializar.
  Evidencia: `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:15-33,40-81`.
- El recurso consulta `LegacyDatabase` directamente. El repositorio localiza
  por username con parámetro y verifica la contraseña contra el hash almacenado.
  Evidencia:
  `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:35`,
  `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:84-98`,
  `auth/src/main/java/com/bcp/workshop/auth/PasswordHasher.java:25-63`.
- No hay `docs/ENDPOINTS.md` para distinguir un contrato acordado del
  comportamiento observado. Las pruebas locales actuales cubren login válido e
  inválido, username con comilla, hashes y migración idempotente:
  `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java:25-149`,
  `auth/src/test/java/com/bcp/workshop/auth/PasswordHasherTest.java:11-35`.
