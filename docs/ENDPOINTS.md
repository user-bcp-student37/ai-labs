# Contratos HTTP

## auth

Base URL local: `http://localhost:8080`. El servicio usa el puerto 8080 en
`auth/src/main/resources/application.properties:1`. Los ejemplos de login usan
las cuentas ficticias locales descritas en `README.md`; el token de respuesta
es una muestra capturada localmente y no debe reutilizarse.

**Estado del contrato:** este documento describe el comportamiento observado en
el código y en las respuestas locales. No se encontró un acuerdo previo con
consumidores externos; las preguntas abiertas se señalan en cada endpoint.

### `GET /q/health`

#### 1. Qué hace

Permite al operador o a un orquestador comprobar si el servicio de autenticación
está disponible.

#### 2. Autenticación

No requiere autenticación. No se exige encabezado `Authorization`.

#### 3. Request

No hay cuerpo ni campos de solicitud. El endpoint está disponible por la
extensión `quarkus-smallrye-health` declarada en
`auth/pom.xml:38-41`; la ruta observada es `/q/health`.

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| — | — | — | La solicitud GET no tiene cuerpo. |

Ejemplo de solicitud completa:

```http
GET /q/health HTTP/1.1
Host: localhost:8080
Accept: application/json
```

#### 4. Response exitosa

El estado HTTP es `200`. En la observación local, el servicio no registró
checks propios: `checks` fue una lista vacía.

| Campo | Tipo | Descripción |
|---|---|---|
| `status` | string | Estado agregado reportado por SmallRye Health. |
| `checks` | array | Checks de salud registrados; actualmente vacío en esta aplicación. |

Ejemplo observado:

```json
{
  "status": "UP",
  "checks": []
}
```

#### 5. Respuestas de error posibles

No se encontró un check de salud propio en `auth/` que produzca un estado
fallido, y durante la observación el endpoint respondió `200`. Si el proceso no
está disponible, no hay respuesta HTTP que documentar. **Pregunta abierta:**
el código actual no permite verificar el estado ni el cuerpo de una respuesta
de salud fallida; no se registra un ejemplo `503` sin un check fallido real.

#### 6. Notas de seguridad

El endpoint no requiere autenticación y revela únicamente estado de salud
agregado en la respuesta observada. No se debe agregar información sensible a
los checks.

### `POST /auth/login`

#### 1. Qué hace

Comprueba las credenciales de una cuenta y, si son válidas, devuelve su perfil
y el token usado por el flujo actual de autenticación.

#### 2. Autenticación

No requiere autenticación previa: este endpoint recibe las credenciales para
iniciar sesión. Enviar `Content-Type: application/json` y, para recibir JSON,
`Accept: application/json`. No se exige encabezado `Authorization`.

#### 3. Request

La ruta y los encabezados JSON están declarados en
`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:15-24`. Los campos
son los miembros públicos de `LoginRequest`; el recurso valida `username` y
`password`, pero no utiliza `client`.

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `username` | string | Sí | Nombre de usuario; no puede ser nulo, vacío ni solo espacios. |
| `password` | string | Sí | Contraseña; no puede ser nula, vacía ni solo espacios. |
| `client` | string | No | Campo aceptado por el DTO, pero no utilizado por el recurso. |

Fuente de tipos: `auth/src/main/java/com/bcp/workshop/auth/LoginRequest.java:3-7`.

Ejemplo completo:

```json
{
  "username": "student",
  "password": "Workshop123!",
  "client": "angular-workshop"
}
```

#### 4. Response exitosa

El estado HTTP es `200`.

| Campo | Tipo | Descripción |
|---|---|---|
| `token` | string | Token generado por el flujo actual. |
| `expiresIn` | number | Tiempo de expiración declarado en segundos; el código devuelve `3600`. |
| `user` | object | Perfil de la cuenta autenticada. |
| `user.username` | string | Nombre de usuario. |
| `user.displayName` | string | Nombre visible; se escapa con HTML 4 antes de responder. |
| `user.role` | string | Rol de la cuenta. |
| `debug` | string | Indicador fijo del flujo actual: `authenticated-with-legacy-flow`. |

La construcción de la respuesta está en
`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:39-50`.

Ejemplo completo capturado en una ejecución local:

```json
{
  "expiresIn": 3600,
  "debug": "authenticated-with-legacy-flow",
  "user": {
    "username": "student",
    "displayName": "Workshop Student",
    "role": "STUDENT"
  },
  "token": "c3R1ZGVudHxTVFVERU5UfDE3OTMwNTQ4MTR8V09SS1NIT1BfU0VDUkVUXzIwMjY="
}
```

El valor de `token` es dinámico; la muestra caduca y no debe tratarse como una
credencial vigente.

#### 5. Respuestas de error posibles

| Código | Cuándo ocurre | Ejemplo de cuerpo |
|---|---|---|
| `400` | Cuerpo JSON nulo o cuerpo vacío, que se interpreta como solicitud nula. | `{"message":"Request is null"}` |
| `400` | `username` ausente, nulo o solo espacios. | `{"message":"Username is required"}` |
| `400` | `password` ausente, nula o solo espacios, después de validar el usuario. | `{"message":"Password is required"}` |
| `400` | JSON mal formado. El servidor local respondió sin cuerpo. | *(cuerpo vacío)* |
| `401` | Usuario inexistente o contraseña incorrecta. El mensaje incluye el username enviado. | `{"message":"Invalid user missing-user or password"}` |
| `405` | Se envía `GET` a `/auth/login`, que declara `POST`. | *(cuerpo vacío)* |
| `406` | El cliente solicita un tipo de respuesta incompatible, por ejemplo `Accept: text/plain`. | *(cuerpo vacío)* |
| `415` | El cliente envía un tipo de contenido distinto de JSON, por ejemplo `Content-Type: text/plain`. | *(cuerpo vacío)* |
| `500` | Una excepción llega al `catch` del recurso. Los valores de `message` y `exception` dependen de la excepción; este ejemplo se observó con una fixture local de base de datos inconsistente. | `{"exception":"java.lang.NullPointerException","message":"Unknown error"}` |

Las respuestas `400`, `401` y `500` construidas por el recurso están en
`auth/src/main/java/com/bcp/workshop/auth/AuthResource.java:26-58`. Las
respuestas sin cuerpo de negociación HTTP y método se observaron localmente;
no tienen un cuerpo JSON definido por esta clase.

#### 6. Notas de seguridad

- El token actual es Base64 de texto concatenado, no una firma criptográfica.
  Incluye un secreto constante en el código, y aunque contiene una expiración,
  este servicio no verifica aquí la firma ni la expiración del token.
  Evidencia: `auth/src/main/java/com/bcp/workshop/auth/LegacyTokenUtil.java:8-15`.
- **Pregunta abierta:** no se confirmó el acuerdo de compatibilidad del token
  con consumidores externos. No cambiar su formato sin coordinarlo con ellos.
- La respuesta `500` expone el mensaje y la clase de la excepción. El `401`
  incluye el username recibido. Ambos comportamientos son los observados en el
  código actual; no se deben asumir como mensajes seguros o estables.
- CORS está habilitado para cualquier origen mediante una expresión general:
  `auth/src/main/resources/application.properties:4-7`.

## Documentos y evidencia consultados

- `README.md`: URL local, cuenta ficticia y forma de ejecutar el servicio.
- `RETO.md`: áreas de autenticación que deben investigarse.
- `docs/GOOD_PRACTICES.md`: prácticas esperadas para tokens, errores y datos.
- `HALLAZGOS.md` y `PLAN.md`: estado y contexto de los hallazgos de auth.
- Código de `auth/`: `AuthResource`, `LoginRequest`, `UserRecord`,
  `LegacyTokenUtil`, `application.properties` y `pom.xml`.
- Respuestas HTTP observadas localmente para health, login exitoso, errores de
  validación, credenciales inválidas, negociación de contenido, método no
  permitido y una excepción capturada.
