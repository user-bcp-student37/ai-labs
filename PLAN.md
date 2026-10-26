# Plan

## auth

### Alcance y precondiciones

- **Selección de este plan:** H-AUTH-02, H-AUTH-04, H-AUTH-05, H-AUTH-06 y
  H-AUTH-07, porque son los hallazgos marcados `Pendiente` en
  `HALLAZGOS.md`. H-AUTH-01 y H-AUTH-03 ya constan como `Resuelto`; sus
  apartados se conservan como historial y no se vuelven a planificar.
  La propuesta no es aprobación adicional de implementación.
- No existe `docs/ENDPOINTS.md`. Se toma como comportamiento observado
  `POST /auth/login`: JSON; `400` para solicitud/campos requeridos ausentes;
  `401` para credenciales no válidas; `200` con `token`, `expiresIn`, `user`
  y `debug` para credenciales válidas; `500` ante excepciones que llegan al
  recurso, con `message` y `exception`. Evidencia:
  `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:15-58`.
- Antes de cambiar, caracterizar el estado actual. Mantener ruta, método,
  campos y estados observados. Los cambios de formato del token, orígenes CORS
  y cuerpo del `500` requieren las decisiones y coordinaciones indicadas en
  sus apartados; no se implementarán de forma que se asuma una compatibilidad
  todavía no acordada.
- Aplicar las convenciones de `docs/GOOD_PRACTICES.md`: Resource → Service →
  Repository, DTO de salida, hash lento con salt, token firmado con expiración
  y claims, configuración externa, SQL parametrizado y errores genéricos.
- Mantener métodos de una responsabilidad, reutilizar lógica, evitar
  anidamiento profundo y usar constantes nombradas.
- **Estado de aprobación:** H-AUTH-01 a H-AUTH-07 están aprobados por
  `rauljaguirre`, quien revisó los siete casos el 2026-10-26.

### H-AUTH-01 — SQL: concatenación de credenciales (Resuelto; historial)

- **Estado actual:** `Resuelto`, según `HALLAZGOS.md`. El siguiente detalle
  conserva la propuesta original, ya implementada; no es parte del alcance
  pendiente de este plan.
- **Hallazgo y problema original:** `LegacyDatabase.findByCredentials`
  concatenaba usuario y contraseña en SQL y ejecutaba con `Statement`.
  Evidencia original: `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:31-35`;
  el recurso pasaba los campos en `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:35`.
- **Cambio propuesto:** sustituir la consulta por `PreparedStatement` con
  parámetros para ambos campos; conservar columnas retornadas y el resultado
  `UserRecord` para la fila coincidente.
- **Archivos previstos:** `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`;
  `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java` y, si se
  separa la prueba de persistencia, un test dedicado bajo
  `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes del cambio:** probar por HTTP credenciales ficticias
  válidas (`student` / `Workshop123!`), inválidas y campos vacíos, anotando
  estados y forma de respuesta. Tras parametrizar, agregar un caso de
  repositorio con un usuario de fixture cuyo nombre literal contiene una
  comilla, insertado como dato de prueba, y verificar que solo autentica la
  pareja exacta; no usar cargas de explotación.
- **Compatibilidad:** mantener `/auth/login`, campos JSON y estados observados.

### H-AUTH-02 — Token Base64 con secreto embebido

- **Hallazgo y problema:** el token codifica texto Base64 con usuario, rol,
  expiración y secreto fijo; Base64 no firma ni protege integridad.
  Evidencia: `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:7-15`;
  creación en `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:39-42`.
- **Cambio propuesto:** reemplazar el formato casero por un token firmado,
  con expiración y claims explícitos, y cargar la clave desde configuración
  externa; no conservar secretos en código. Evaluar extensión Quarkus JWT u
  opción ya disponible antes de agregar dependencias y justificar cualquier
  alta en `auth/pom.xml`.
- **Archivos previstos:** `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java`
  o nueva clase de seguridad; `auth/src/main/resources/application.properties`;
  `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java` si cambia la
  integración; `auth/pom.xml` solo si la opción elegida requiere dependencia;
  pruebas bajo `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes del cambio:** verificar login válido, tipo y
  presencia de `token`, `expiresIn` observado como 3600 y claims que pueden
  leerse en el formato actual, sin fijar el token dinámico ni tratar el secreto
  legacy como contrato. Después, verificar firma, claims y expiración con
  pruebas locales de la implementación elegida; usar una clave de prueba
  aislada, no un secreto real.
- **Compatibilidad pendiente:** conservar la clave `token` y `expiresIn` en
  la respuesta. El contenido cambia; coordinar la aceptación del token con
  sus consumidores fuera de auth antes de implementar y no modificar esos
  componentes en este alcance.

### H-AUTH-03 — Contraseñas en texto plano (Resuelto; historial)

- **Estado actual:** `Resuelto`, según `HALLAZGOS.md`. El siguiente detalle
  conserva la propuesta original, ya implementada; no es parte del alcance
  pendiente de este plan.
- **Hallazgo y problema original:** el esquema almacenaba contraseña como
  texto y se insertaban cuentas ficticias con secretos literales.
  Evidencia original: `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:22-24`;
  comparación original en `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:32`.
- **Cambio propuesto:** persistir hashes lentos con salt individual y verificar
  mediante una función dedicada, nunca comparando texto plano. Evaluar una
  implementación disponible en el stack; si se usa PBKDF2 del JDK, nombrar
  parámetros de trabajo mediante constantes. Diseñar migración idempotente de
  bases locales ya creadas, sin perder cuentas ni cambiar credenciales de
  acceso; no registrar contraseñas.
- **Archivos previstos:** `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`
  o repositorio resultante; nuevo componente de hashing en
  `auth/src/main/java/com/bcp/workshop/auth/`; configuración o
  `auth/pom.xml` solo si una dependencia resulta necesaria y se justifica;
  pruebas bajo `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes del cambio:** cubrir login válido con usuario
  sembrado, contraseña incorrecta y usuario inexistente. Añadir pruebas de
  persistencia/migración que demuestren que la contraseña no queda almacenada
  en claro, que cada hash tiene salt y que la verificación acepta solo la
  contraseña correcta.
- **Compatibilidad:** mantener los resultados HTTP y la respuesta de login
  observados. La estrategia de actualización de bases existentes debe quedar
  probada antes de reemplazar el formato.

### H-AUTH-04 — CORS con origen demasiado amplio

- **Hallazgo y problema:** CORS está habilitado y permite cualquier origen
  mediante una expresión general. Evidencia:
  `auth/src/main/resources/application.properties:4-7`.
- **Cambio propuesto:** reemplazar el comodín por una lista explícita y
  configurable por entorno. README documenta el frontend local en
  `http://localhost:4200`; el origen de producción no está documentado y debe
  confirmarse con quien opera/despliega el servicio antes de habilitarlo.
- **Archivos previstos:** `auth/src/main/resources/application.properties`;
  pruebas de configuración HTTP bajo `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes del cambio:** probar preflight desde origen local
  permitido y desde origen arbitrario, registrar cabeceras y comportamiento
  actual. Después, comprobar que el origen acordado recibe cabeceras CORS y
  que un origen no autorizado no las recibe.
- **Compatibilidad pendiente:** restringir CORS cambia el comportamiento
  observado para otros orígenes. Acordar y documentar la lista de orígenes
  válidos por entorno antes de cambiar configuración; no inventar el origen
  de producción.

### H-AUTH-05 — Errores exponen detalles internos

- **Hallazgo y problema:** el recurso devuelve mensaje de excepción y clase;
  la persistencia imprime excepciones completas.
  Evidencia: `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:54-58`;
  `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java:35-36,95-96`.
- **Cambio propuesto:** devolver un mensaje genérico al cliente y conservar
  solo el estado de error necesario; registrar detalles del lado servidor con
  logger controlado, sin exponer credenciales ni tokens. Eliminar
  `printStackTrace`.
- **Archivos previstos:** `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java`;
  `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java` o repositorio
  resultante; pruebas bajo `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes del cambio:** con un test unitario local y un
  repositorio de prueba que provoque una excepción, registrar estado y cuerpo
  `500` actuales; cubrir también `400`, `401` y `200` para evitar cambios
  laterales en el contrato.
- **Compatibilidad pendiente:** el `500` actual incluye `exception` y mensaje
  interno. La respuesta segura debe dejar de revelar esos valores; acordar
  explícitamente el cuerpo genérico antes de implementar. Mantener `500` y
  JSON salvo que un contrato acordado indique otra cosa.

### H-AUTH-06 — Dependencias candidatas a revisión SCA

- **Hallazgo y problema:** el POM declara Quarkus 3.27.4 y Commons Text 1.9;
  no se verificó si hay advisory aplicable, por lo que no se afirma una CVE.
  Evidencia: `auth/pom.xml:13,49-50`.
- **Cambio propuesto:** ejecutar el análisis SCA disponible en el repositorio
  y contrastar advisories aplicables, versiones transitivas y compatibilidad
  con Quarkus/JDK. Actualizar o retirar dependencia únicamente con evidencia;
  no silenciar CodeQL ni Dependency Review. No incorporar herramienta o
  dependencia nueva sin justificarla.
- **Archivos previstos:** primero, reporte/evidencia del análisis (en la
  actualización de este apartado de `PLAN.md` y, si se confirma un advisory,
  su resultado en `HALLAZGOS.md`); `auth/pom.xml` solo si un hallazgo
  confirmado requiere actualización o eliminación; pruebas del módulo si el
  cambio afecta comportamiento. No crear otro artefacto de evidencia fuera de
  las ubicaciones permitidas.
- **Caracterización antes del cambio:** registrar versiones efectivas del
  árbol de dependencias y resultado de las fuentes/scanners disponibles antes
  de modificarlas. Como línea base, ejecutar `mvn dependency:tree` y `mvn
  test` desde `auth/`; registrar versiones y resultado, sin inventar resultados
  de scanners. El POM revisado no declara una herramienta SCA; no añadir una
  dependencia ni silenciar controles. Si no hay advisory confirmado,
  documentar que no hay base para cambiar versiones y no tocar el POM. Tras
  una actualización justificada, repetir el análisis y ejecutar las pruebas
  de auth.
- **Resultado alternativo:** si no se confirma advisory aplicable, no cambiar
  versiones por conjetura y actualizar el estado de H-AUTH-06 con evidencia.

### H-AUTH-07 — Resource mezcla responsabilidades

- **Hallazgo y problema:** `login` valida, consulta persistencia, crea token y
  construye respuesta. Evidencia:
  `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:24-49`.
- **Cambio propuesto:** separar responsabilidades según
  `docs/GOOD_PRACTICES.md`: Resource para HTTP, Service para reglas del login,
  Repository para persistencia, DTO propio para respuesta. Extraer validación
  sin duplicarla; usar guard clauses y constantes para expiración y otros
  valores actualmente literales.
- **Archivos previstos:** `auth/src/main/java/com/bcp/workshop/auth/AuthResource.java`;
  `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java` y/o nuevo
  repositorio; nuevas clases de servicio y DTO en
  `auth/src/main/java/com/bcp/workshop/auth/`; pruebas bajo
  `auth/src/test/java/com/bcp/workshop/auth/`.
- **Caracterización antes del cambio:** completar pruebas HTTP de solicitud
  nula/mal formada cuando sea representable, campos requeridos ausentes,
  credenciales válidas e inválidas, y respuesta de éxito completa (`token`,
  `expiresIn`, campos de `user` y `debug`). Registrar estados y campos actuales
  antes de mover lógica; preservar el escape de `displayName` y el campo
  `client` actualmente aceptado aunque no se use.
- **Orden y compatibilidad:** H-AUTH-01 y H-AUTH-03 ya están resueltos. Hacer
  esta separación después de caracterizar y acordar las decisiones de
  compatibilidad de H-AUTH-02 y H-AUTH-05, para evitar duplicar cambios en el
  mismo método. Mantener ruta y comportamiento observado, respetando las
  decisiones explícitas de esos hallazgos.

### Secuencia, validación y decisiones pendientes

1. Escribir y ejecutar pruebas de caracterización antes de refactorizar o
   cambiar persistencia, token o errores; registrar resultados reales.
2. H-AUTH-01 y H-AUTH-03 están resueltos. H-AUTH-02 requiere coordinar la
   aceptación del nuevo formato con consumidores del token fuera de auth;
   H-AUTH-04 requiere confirmar orígenes permitidos; H-AUTH-05 requiere acordar
   el cuerpo genérico de error. Estas precondiciones no autorizan cambios fuera
   del componente.
3. Implementar en cambios revisables; ejecutar `mvn test` desde `auth/` y
   después `mvn verify` para generar JaCoCo. Meta del código modificado:
   cobertura de 85% o superior, sin reducir gates.
4. `HALLAZGOS.md` registra como Resueltos H-AUTH-01 y H-AUTH-03 con evidencia.
   Actualizar `docs/TESTING.md` en su paso documental con resultados reales;
   todavía no se crea ese archivo.

### Ejecuciones registradas

- **Actualización del plan — H-AUTH-02, H-AUTH-04, H-AUTH-05, H-AUTH-06 y
  H-AUTH-07:** se actualizó este documento tras revisar `HALLAZGOS.md`,
  `RETO.md`, `docs/GOOD_PRACTICES.md` y el código pertinente de `auth/`.
  No se modificó código ni se ejecutaron pruebas; esta actualización es
  documental.
- **H-AUTH-01 — caracterización, intento inicial:** `mvn test` se lanzó desde
  la raíz del repositorio por error de directorio; Maven terminó con
  `MissingProjectException` porque allí no hay POM. No se ejecutaron pruebas
  de auth.
- **H-AUTH-01 — caracterización previa:** `Set-Location .\\auth; mvn test`
  pasó (3 pruebas, 0 fallos, 0 errores). El usuario ficticio con comilla
  obtuvo el `401` observado; SQLite registró un error de sintaxis. La prueba
  se actualizó como regresión para exigir que la credencial literal autentique.
- **H-AUTH-01 — primera regresión posterior:** `Set-Location .\\auth; mvn test`
  falló al compilar porque se había quitado el import `Statement` que aún usa
  la inicialización de tablas. Se restauró ese import; esta ejecución no llegó
  a correr pruebas.
- **H-AUTH-01 — regresión posterior:** `Set-Location .\\auth; mvn test` pasó
  (3 pruebas, 0 fallos, 0 errores). El usuario de fixture con nombre literal
  que contiene comilla inició sesión con `200`; login válido e inválido
  conservaron sus resultados probados.
- **H-AUTH-01 — cobertura, primer verify:** `Set-Location .\\auth; mvn verify`
  terminó con BUILD SUCCESS y 3 pruebas aprobadas bajo Maven/JDK 25. JaCoCo
  0.8.12 emitió errores de instrumentación por class file major version 68;
  esa cobertura no se considera válida para el gate.
- **H-AUTH-01 — cobertura, verify repetido con JDK 21:** establecí
  `JAVA_HOME=C:\\Program Files\\Eclipse Adoptium\\jdk-21.0.12.101-hotspot`,
  antepuse su `bin` a `PATH` y ejecuté `Set-Location .\\auth; mvn verify`.
  BUILD SUCCESS; 3 pruebas aprobadas; JaCoCo generó
  `auth/target/site/jacoco/index.html`. `LegacyDatabase`: 21/24 líneas
  cubiertas (87.5%), sobre el 85% requerido. CodeQL y Dependency Review
  remotos no se ejecutaron.
- **H-AUTH-03 — caracterización previa:** con JDK 21, `Set-Location .\\auth;
  mvn test` pasó (4 pruebas, 0 fallos, 0 errores). La prueba nueva confirma
  que la contraseña sembrada de `student` estaba almacenada en texto plano;
  el login válido, inválido y el caso de usuario con comilla también pasaron.
- **H-AUTH-03 — primera regresión posterior:** con JDK 21, `mvn test` tuvo
  1 fallo entre 7 pruebas: el test de hash consultó la base antes de que el
  bean lazy ejecutara su inicialización. La prueba ahora invoca la inicialización
  para caracterizar la migración de arranque; repetir el test.
- **H-AUTH-03 — regresión posterior:** con JDK 21, `Set-Location .\\auth;
  mvn test` pasó (9 pruebas, 0 fallos, 0 errores), cubriendo login válido e
  inválido, username literal con comilla, almacenamiento hash, migración
  idempotente y verificación PBKDF2.
- **H-AUTH-03 — cobertura:** con JDK 21, `Set-Location .\\auth; mvn verify`
  terminó BUILD SUCCESS con 9 pruebas aprobadas. JaCoCo: `LegacyDatabase`
  50/54 líneas (92.6%); `PasswordHasher` 47/49 (95.9%). No se añadieron
  dependencias. CodeQL y Dependency Review remotos no se ejecutaron.
