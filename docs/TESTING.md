# Evidencia de pruebas

## auth

Las pruebas verifican los endpoints documentados en
[`ENDPOINTS.md`](./ENDPOINTS.md). Se ejecutan desde `auth/` con JDK 21. Los
casos de contrato no implican que los hallazgos de seguridad pendientes estén
corregidos.

### Matriz de casos

| Endpoint | Caso | Tipo | Resultado esperado |
|---|---|---|---|
| `GET /q/health` | `reportsHealthyStatus` | Camino feliz | `200`, `status` igual a `UP`. |
| `GET /q/health` | `reportsNoChecksWhenNoneAreRegistered` | Borde | `200`, `checks` es una lista vacía. |
| `GET /q/health` | Estado de salud fallido | Pendiente | `ENDPOINTS.md` deja abierto el comportamiento porque auth no registra un health check que pueda fallar. No se inventa una respuesta `503`. |
| `POST /auth/login` | `logsInWithWorkshopUser` | Camino feliz | `200`; verifica `token`, `expiresIn`, `user` y `debug`. |
| `POST /auth/login` | `logsInWhenOptionalClientIsOmitted` | Borde | `200`; `client` es opcional. |
| `POST /auth/login` | `logsInWithUsernameContainingAQuote` | Borde — H-AUTH-01 | `200` para el username literal del fixture. |
| `POST /auth/login` | `rejectsNullRequest` | Error `400` | `message` es `Request is null`. |
| `POST /auth/login` | `rejectsEmptyRequestBody` | Error `400` | `message` es `Request is null`. |
| `POST /auth/login` | `rejectsMalformedJson` | Error `400` | Cuerpo vacío, como se observó en Quarkus. |
| `POST /auth/login` | `rejectsMissingUsername` | Error `400` | `message` es `Username is required`. |
| `POST /auth/login` | `rejectsBlankUsername` | Error `400` | `message` es `Username is required`. |
| `POST /auth/login` | `rejectsMissingPassword` | Error `400` | `message` es `Password is required`. |
| `POST /auth/login` | `rejectsBlankPassword` | Error `400` | `message` es `Password is required`. |
| `POST /auth/login` | `rejectsIncorrectPassword` | Error `401` | `message` es `Invalid user student or password`. |
| `POST /auth/login` | `rejectsUnknownUsername` | Error `401` | `message` incluye el username enviado. |
| `POST /auth/login` | `rejectsUnsupportedHttpMethod` | Error `405` | Cuerpo vacío para `GET /auth/login`. |
| `POST /auth/login` | `rejectsUnsupportedAcceptType` | Error `406` | Cuerpo vacío cuando se envía `Accept: text/plain`. |
| `POST /auth/login` | `rejectsUnsupportedRequestContentType` | Error `415` | Cuerpo vacío cuando se envía `Content-Type: text/plain`. |
| `POST /auth/login` | `returnsObservedInternalErrorResponseWhenUserRecordIsMalformed` | Error `500` — H-AUTH-05 | Verifica `exception` y `message` con un repositorio simulado que devuelve un registro inválido. |

### Código de los tests

El código completo y ejecutable, incluidos imports y fixtures, se mantiene en
[`AuthResourceTest.java`](../auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java)
y [`HealthEndpointTest.java`](../auth/src/test/java/com/bcp/workshop/auth/HealthEndpointTest.java).
Las pruebas adicionales de almacenamiento/migración de contraseñas y del
hasher están en
[`PasswordHasherTest.java`](../auth/src/test/java/com/bcp/workshop/auth/PasswordHasherTest.java)
y `AuthResourceTest.java` (H-AUTH-03).

Ejemplo del caso de error `500` que caracteriza el cuerpo documentado; el
registro con `displayName` nulo se inyecta solo en el test para alcanzar el
`catch`, no se modifica ni se oculta el comportamiento del servicio:

```java
QuarkusMock.installMockForType(new LegacyDatabase() {
    @Override
    public UserRecord findByCredentials(String username, String password) {
        return new UserRecord(1, username, null, "STUDENT");
    }
}, LegacyDatabase.class);

given()
        .contentType("application/json")
        .body("{\"username\":\"student\",\"password\":\"Workshop123!\"}")
        .when().post("/auth/login")
        .then()
        .statusCode(500)
        .body("exception", is("java.lang.NullPointerException"))
        .body("message", is("Unknown error"));
```

### Ejecuciones y cobertura

| Componente e IDs | Comando y directorio | Código de salida | Resultado |
|---|---|---:|---|
| auth; contrato de `GET /q/health` y `POST /auth/login`; H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-05 | `mvn test` desde `auth/`, JDK 21 | `1` | Exploración inicial: 24 tests, 1 fallo. `HealthEndpointTest.rejectsUnsupportedAcceptType` esperaba `406` para `GET /q/health` con `Accept: text/plain`, pero el endpoint devolvió `200`. Este comportamiento no estaba especificado como error en `ENDPOINTS.md`; el test exploratorio no se conservó ni se cambió su expectativa. Se registra abajo como pendiente de contrato. |
| auth; contrato de endpoints; H-AUTH-01, H-AUTH-02, H-AUTH-03, H-AUTH-05 | `mvn verify` desde `auth/`, JDK 21 | `0` | `BUILD SUCCESS`; 23 tests, 0 fallos, 0 errores, 0 omitidos. |

Comando usado para la ejecución aprobada, desde la raíz del repositorio:

```powershell
Set-Location .\auth
$env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot'
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
mvn verify
```

JaCoCo `0.8.12` produjo
[`auth/target/site/jacoco/index.html`](../auth/target/site/jacoco/index.html)
y `jacoco.xml`. Método: cobertura de líneas JaCoCo por clase, calculada como
líneas cubiertas / (líneas cubiertas + líneas no cubiertas). Resultados:

| Clase de producción | Líneas cubiertas | Cobertura |
|---|---:|---:|
| `AuthResource` | `25/25` | `100.0%` |
| `LegacyDatabase` | `50/54` | `92.6%` |
| `PasswordHasher` | `47/49` | `95.9%` |

`AuthResource` tuvo además 13/14 ramas cubiertas (92.9%). No se modificó código
de producción en este paso; la tabla informa la cobertura de las clases
ejercitadas por las pruebas de auth. La meta documentada para código modificado
es al menos 85%.

### Fallos, pendientes y pruebas propuestas

- **Fallo exploratorio:** el endpoint health respondió `200` para
  `Accept: text/plain`, no el `406` supuesto por el test preliminar. No se
  considera un defecto confirmado porque ese error no está definido en
  `ENDPOINTS.md`; tampoco se retuvo un test que impusiera ese comportamiento.
- **Pendiente:** no hay un health check que permita verificar una respuesta
  fallida de `/q/health`. No se añadió uno solo para fabricar un `503`.
- **Pendiente:** el formato y la validación del token siguen siendo los
  observados y no firmados (H-AUTH-02); no se prueba compatibilidad con
  consumidores externos.
- **Pendiente:** no se ejecutaron CodeQL ni Dependency Review remotos, ni un
  análisis de advisories para H-AUTH-06.
- **Propuestas:** si se define un health check que pueda fallar, agregar la
  prueba de su respuesta real; si se acuerda un contrato de negociación para
  `Accept: text/plain` en health, actualizar primero `ENDPOINTS.md` y luego
  probarlo. Los cambios de H-AUTH-02, H-AUTH-04, H-AUTH-05 y H-AUTH-07 requieren
  sus precondiciones de `PLAN.md` y pruebas de caracterización antes de
  implementarse.
