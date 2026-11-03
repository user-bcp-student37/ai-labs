# Contratos de endpoints

Este documento describe el contrato de cada componente. Hoy solo existe la sección de `api`. Las secciones de `auth` y `web` se agregarán al documentarse sus componentes.

## Estado de cada contrato

- **Contrato observado**: lo que hace el código actual en `api/app/main.py`, `api/app/schemas.py` y `api/app/repository.py`. Se verificó ejecutando las rutas con `TestClient` sobre una base temporal (no sobre la base de trabajo). Los casos marcados "por código, no probado" no se ejecutaron.
- **Contrato acordado**: ninguno todavía. Las decisiones pendientes están en [HALLAZGOS.md](../HALLAZGOS.md) y [PLAN.md](../PLAN.md).
- **Riesgos pendientes**: se listan por endpoint y en la sección final de preguntas abiertas.

## Componente api

### Autenticación del componente api

Todos los endpoints de `api` requieren el header:

```
Authorization: Bearer <token>
```

El token es el Base64 estándar de la cadena `usuario|rol|exp|secreto`:

- `usuario`: nombre de usuario que se usa como identidad.
- `rol`: texto libre; la API no lo valida.
- `exp`: expiración en segundos Unix (entero). Debe ser mayor o igual que la hora actual.
- `secreto`: debe coincidir con la constante `LEGACY_SECRET` de `api/app/main.py:20`. No se documenta aquí.

Validación observada en `api/app/main.py:23-32`: se quita el prefijo `Bearer `, se decodifica Base64, se separan cuatro partes con `|` y se comprueban el secreto y la expiración. Cualquier fallo responde 401 con `detail` `"Invalid token: " + str(error)`.

`api` no tiene ruta de login. El token lo emite el componente `auth/`.

Riesgo abierto: el token no tiene firma y el secreto está embebido en el código. Cualquiera que conozca la constante puede fabricar un token con otro usuario o rol (H-API-01, pendiente de coordinación con `auth/`).

### Respuestas de error comunes a todos los endpoints

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Falta el header, el token no tiene cuatro partes, el secreto no coincide, la expiración ya pasó o el Base64 es inválido | `{"detail": "Invalid token: invalid token"}` |

Verificado con ejecución: sin header, con secreto incorrecto, con `exp` vencido y con token `!!!` devuelven exactamente ese cuerpo.

Pregunta abierta: con Base64 inválido, el texto de `str(error)` puede variar porque ahí se concatena la excepción original (`api/app/main.py:32`). El cuerpo exacto de ese caso no se verificó.

---

### 1. GET /api/tasks

**Qué hace**: devuelve las tareas de un usuario. Si no se indica `owner`, devuelve las del usuario del token.

**Autenticación**: sí. Header `Authorization: Bearer <token>` (ver sección anterior).

**Request**

Parámetros de query:

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `owner` | string | No | Usuario cuyas tareas se listan. Si está vacío o no se envía, se usa el usuario del token (`api/app/main.py:89`). |

Ejemplo real (token de `student`, sin `owner`):

```http
GET /api/tasks HTTP/1.1
Authorization: Bearer <token de student>
```

**Respuesta exitosa**

Código: `200 OK`. Cuerpo: arreglo de tareas ordenado por `id` ascendente (`api/app/repository.py:8-10`).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador autoincremental. |
| `title` | string | Título de la tarea. |
| `description` | string | Descripción de la tarea. |
| `status` | string | Estado libre; valores observados: `TODO`, `IN_PROGRESS`, `DONE`, `ARCHIVED`. |
| `owner` | string | Usuario dueño de la tarea. |
| `priority` | string | Prioridad libre; valores observados: `LOW`, `MEDIUM`, `HIGH`. |
| `createdAt` | string | Fecha de creación en formato `YYYY-MM-DD HH:MM:SS`, generada por SQLite `datetime('now')` (UTC). |

Ejemplo real (`GET /api/tasks`, token de `student`):

```json
[
  {
    "id": 1,
    "title": "Refactor login",
    "description": "Separar responsabilidades en frontend",
    "status": "TODO",
    "owner": "student",
    "priority": "HIGH",
    "createdAt": "2026-11-02 22:03:56"
  },
  {
    "id": 2,
    "title": "Review API",
    "description": "Revisar seguridad de endpoints",
    "status": "IN_PROGRESS",
    "owner": "student",
    "priority": "MEDIUM",
    "createdAt": "2026-11-02 22:03:56"
  }
]
```

Nota: la fecha de los ejemplos proviene de una ejecución de prueba. En una base real será distinta.

Si no hay tareas para el usuario, la respuesta es `200` con `[]` (por código, no probado; la consulta devuelve una lista vacía).

**Errores posibles**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Token inválido o ausente (ver errores comunes). | `{"detail": "Invalid token: invalid token"}` |

**Notas de seguridad**

- **Autorización por parámetro (H-API-05, alta, pendiente)**: `owner` reemplaza la identidad del token (`api/app/main.py:89`). Verificado: con un token de `student`, `GET /api/tasks?owner=trainer` devuelve la tarea de `trainer`. Cualquier usuario autenticado puede leer las tareas de otro.
- Lo esperado tras corregir H-API-05 (no acordado): la autorización debe depender solo de la identidad del token. Queda como pregunta abierta si un rol de trainer puede consultar otros owners.

---

### 2. POST /api/tasks

**Qué hace**: crea una tarea. El dueño por defecto es el usuario del token.

**Autenticación**: sí. Header `Authorization: Bearer <token>`.

**Request**

Cuerpo JSON (objeto). Validado con el modelo `NewTaskPayload` (`api/app/schemas.py:11-21`). Todos los campos se convierten a texto con `str()`.

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `title` | string | No (defecto `""`) | Título de la tarea. Se acepta vacío (H-API-12). |
| `description` | string | No (defecto `""`) | Descripción de la tarea. |
| `status` | string | No (defecto `TODO`) | Estado. No hay lista de valores válidos (H-API-12). |
| `priority` | string | No (defecto `MEDIUM`) | Prioridad. No hay lista de valores válidos (H-API-12). |
| `owner` | string o null | No (defecto usuario del token) | Dueño de la tarea. Si es `null`, se guarda el texto `"None"` (verificado). |

Ejemplo real:

```http
POST /api/tasks HTTP/1.1
Authorization: Bearer <token de student>
Content-Type: application/json

{
  "title": "Demo",
  "description": "Desc",
  "status": "TODO",
  "priority": "HIGH"
}
```

Ejemplo mínimo válido (usa defectos):

```json
{ "title": "Solo titulo" }
```

**Respuesta exitosa**

Código: `201 Created`. Cuerpo: la tarea creada, con la misma forma que en `GET /api/tasks`.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | integer | Identificador asignado. |
| `title` | string | Título guardado. |
| `description` | string | Descripción guardada. |
| `status` | string | Estado guardado. |
| `owner` | string | Dueño guardado. |
| `priority` | string | Prioridad guardada. |
| `createdAt` | string | Fecha de creación `YYYY-MM-DD HH:MM:SS`. |

Ejemplo real (respuesta al request anterior):

```json
{
  "id": 4,
  "title": "Demo",
  "description": "Desc",
  "status": "TODO",
  "owner": "student",
  "priority": "HIGH",
  "createdAt": "2026-11-02 22:03:56"
}
```

Ejemplos reales de otros casos verificados:

- Sin `description` ni `status`: `{"id": 5, "title": "Solo titulo", "description": "", "status": "TODO", "owner": "student", "priority": "MEDIUM", ...}`.
- Con `"owner": null`: `"owner": "None"` (texto literal).
- Con `"title": 5`: `"title": "5"` (conversión a texto).

**Errores posibles**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Token inválido o ausente. | `{"detail": "Invalid token: invalid token"}` |
| 422 | El cuerpo no es un objeto JSON (por ejemplo, un arreglo). Verificado con `["x"]`. | Ver cuerpo abajo. |

Cuerpo 422 (verificado con body `["x"]`; el `input` refleja el valor enviado):

```json
{
  "detail": [
    {
      "type": "model_attributes_type",
      "loc": ["body"],
      "msg": "Input should be a valid dictionary or object to extract fields from",
      "input": ["x"]
    }
  ]
}
```

Sin JSON válido o con `Content-Type` distinto de JSON: 422 por la validación estándar de FastAPI (por código, no probado; el cuerpo exacto no se documenta).

**Notas de seguridad**

- **Autorización por campo `owner` del body (H-API-05, alta, pendiente)**: `owner` reemplaza la identidad del token (`api/app/main.py:94`). Verificado en el código, no ejecutado: un usuario puede crear tareas a nombre de otro.
- **Validación incompleta (H-API-12, media, pendiente)**: `title` vacío y valores arbitrarios de `status` y `priority` se aceptan. El resumen puede contar valores fuera del dominio.
- **Conversión a texto**: `owner: null` se guarda como `"None"`, lo que crea tareas de un owner ficticio. Ver preguntas abiertas.
- Las consultas usan parámetros (`api/app/repository.py:25`); no hay inyección SQL en este endpoint (H-API-03, resuelto).

---

### 3. GET /api/summary

**Qué hace**: devuelve un resumen de tareas de un usuario: total, conteo por estado y número de tareas de alta prioridad abiertas.

**Autenticación**: sí. Header `Authorization: Bearer <token>`.

**Request**

Parámetros de query:

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `owner` | string | No | Usuario a resumir. Si está vacío o no se envía, se usa el usuario del token (`api/app/main.py:100`). |

Ejemplo real:

```http
GET /api/summary HTTP/1.1
Authorization: Bearer <token de student>
```

**Respuesta exitosa**

Código: `200 OK`.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Usuario resumido (el de `owner` o el del token). |
| `total` | integer | Número de tareas del usuario. |
| `byStatus` | objeto `string -> integer` | Conteo de tareas por valor de `status`. Las claves son los estados que existen en la base. |
| `highPriorityOpen` | integer | Número de tareas con `priority` `HIGH` y `status` distinto de `DONE` y `ARCHIVED` (`api/app/main.py:35-36`). |

Ejemplo real:

```json
{
  "owner": "student",
  "total": 5,
  "byStatus": {
    "TODO": 4,
    "IN_PROGRESS": 1
  },
  "highPriorityOpen": 2
}
```

Si el usuario no tiene tareas: `{"owner": "<usuario>", "total": 0, "byStatus": {}, "highPriorityOpen": 0}` (por código, no probado).

**Errores posibles**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Token inválido o ausente. | `{"detail": "Invalid token: invalid token"}` |

**Notas de seguridad**

- **Autorización por parámetro (H-API-05, alta, pendiente)**: `owner` reemplaza la identidad del token (`api/app/main.py:100`). Cualquier usuario autenticado puede obtener el resumen de otro.
- El campo `owner` de la respuesta refleja el parámetro, no el token.

---

### 4. POST /api/requirements

**Qué hace**: guarda un archivo de requerimiento subido por el usuario en el directorio de cargas.

**Autenticación**: sí. Header `Authorization: Bearer <token>`.

**Request**

Cuerpo `multipart/form-data` (`api/app/main.py:105`):

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `file` | archivo | Sí | Archivo a guardar. Se usa su nombre original (`filename`) tal cual. |

Ejemplo real (con `curl`):

```bash
curl -X POST http://localhost:8000/api/requirements \
  -H "Authorization: Bearer <token de student>" \
  -F "file=@req.txt;type=text/plain"
```

El directorio de destino sale de la variable `WORKSHOP_UPLOAD_DIR` (por defecto `./uploads`).

**Respuesta exitosa**

Código: `201 Created`.

| Campo | Tipo | Descripción |
|---|---|---|
| `owner` | string | Usuario del token que subió el archivo. |
| `fileName` | string | Nombre original del archivo, sin normalizar. |
| `storedAt` | string | Ruta completa donde se escribió el archivo. |
| `size` | integer | Tamaño en bytes del contenido leído. |

Ejemplo real (archivo `req.txt` de 4 bytes, ruta de una ejecución en Windows; el separador y el directorio cambian según el sistema):

```json
{
  "owner": "student",
  "fileName": "req.txt",
  "storedAt": "C:\\Users\\Usuario\\AppData\\Local\\Temp\\tmprmf9mr3f\\up\\req.txt",
  "size": 4
}
```

**Errores posibles**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Token inválido o ausente. | `{"detail": "Invalid token: invalid token"}` |
| 422 | Falta el campo `file`. Verificado. | Ver cuerpo abajo. |
| 500 | Falla la escritura en disco (por ejemplo, permisos o nombre inválido). No hay manejo de excepciones en `upload_requirement` (`api/app/main.py:104-109`). | Por código, no probado. FastAPI devuelve su error interno estándar; el cuerpo exacto queda como pregunta abierta. |

Cuerpo 422 cuando falta `file` (verificado):

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "file"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

**Notas de seguridad**

- **Path traversal (H-API-06, alta, pendiente)**: `file.filename` se usa sin normalizar en `Path(selected_uploads) / str(file.filename)` (`api/app/main.py:106`). Un nombre con separadores de ruta puede escribir fuera del directorio de cargas. No se reprodujo en ejecución.
- **Sin límite de tamaño**: el contenido se lee completo en memoria (`api/app/main.py:107`).
- **Sin lista de extensiones**: se acepta cualquier tipo de archivo.
- **Nombre nulo**: si el cliente no envía nombre, `str(None)` produce el nombre `"None"` (por código, no probado).
- La respuesta expone la ruta absoluta del servidor en `storedAt`.

---

### 5. GET /api/backend-health

**Qué hace**: consulta la salud del backend de autenticación (`AUTH_HEALTH_URL`, por defecto `http://localhost:8080/q/health`) y devuelve el resultado.

**Autenticación**: sí. Header `Authorization: Bearer <token>`.

**Request**

Sin parámetros ni cuerpo.

```http
GET /api/backend-health HTTP/1.1
Authorization: Bearer <token de student>
```

La URL se configura con la variable de entorno `AUTH_HEALTH_URL` (`api/app/main.py:113`). Tiempo de espera: 3 segundos (`api/app/main.py:115`).

**Respuesta exitosa**

Código: `200 OK`. Siempre devuelve `200` si el token es válido, incluso cuando el backend de salud no responde.

| Campo | Tipo | Descripción |
|---|---|---|
| `requestedBy` | string | Usuario del token. |
| `status` | integer | Código HTTP devuelto por el backend de salud. Vale `0` si la llamada falló (conexión rechazada, tiempo agotado u otro error). |
| `body` | string | Cuerpo devuelto por el backend de salud, o el texto del error si la llamada falló. |

Ejemplo real cuando el backend de salud no está activo (verificado):

```json
{
  "requestedBy": "student",
  "status": 0,
  "body": "HTTPConnectionPool(host='localhost', port=8080): Max retries exceeded with url: /q/health (Caused by NewConnectionError(...))"
}
```

El texto completo de `body` depende del sistema operativo y del idioma del mensaje de error; el ejemplo está recortado.

Ejemplo cuando el backend responde (por código, no probado): `{"requestedBy": "student", "status": 200, "body": "<cuerpo del health>"}`.

**Errores posibles**

| Código | Cuándo ocurre | Cuerpo |
|---|---|---|
| 401 | Token inválido o ausente. | `{"detail": "Invalid token: invalid token"}` |

Fallo del backend de salud: no es un error HTTP. Se devuelve `200` con `status: 0` y el detalle de la excepción en `body`.

**Notas de seguridad**

- **Exposición de detalles internos (H-API-09, media, pendiente)**: `body` contiene `str(error)` (`api/app/main.py:118`). Revela host, puerto y texto de la excepción al cliente.
- **Excepciones amplias (H-API-14, baja, pendiente)**: `except Exception` oculta la causa real del fallo (`api/app/main.py:117`).
- La llamada sale del servidor hacia la URL configurada. La URL no se valida; quien controle la variable de entorno controla el destino.

---

## Preguntas abiertas

1. **Contrato acordado**: no hay acuerdo humano sobre ningún endpoint. Hasta haberlo, este documento es contrato observado.
2. **Lista de valores de `status` y `priority`**: el código no restringe valores. ¿Se fijan valores válidos? (H-API-12)
3. **`owner: null` al crear**: hoy se guarda `"None"`. ¿Debe ser un error 422 o usar el usuario del token? (H-API-05, H-API-12)
4. **Parámetro `owner` en listado y resumen**: ¿se elimina, o solo un rol de trainer puede usarlo? (H-API-05)
5. **Límites de archivo**: ¿tamaño máximo y extensiones permitidas? (H-API-06)
6. **Cuerpo del 500 en la carga**: ¿se acuerda un manejo de error explícito? Hoy no existe.
7. **Formato de `createdAt`**: ¿debe ser ISO 8601 con zona horaria? Hoy es `YYYY-MM-DD HH:MM:SS` en UTC sin zona.
8. **Token y coordinación con `auth/`**: el cambio a firma verificable (H-API-01) requiere acordar el formato con `auth/`, que emite el token.
9. **Valor de `owner` vacío**: `?owner=` cae al usuario del token porque `owner or ...` trata la cadena vacía como falsa (`api/app/main.py:89`, `:100`). ¿Es el comportamiento deseado?

## Documentos consultados

- [README.md](../README.md): cómo se ejecuta la API y requisitos de documentación.
- [RETO.md](../RETO.md): hallazgos esperados.
- [docs/GOOD_PRACTICES.md](./GOOD_PRACTICES.md): convenciones de errores y validación.
- [HALLAZGOS.md](../HALLAZGOS.md): IDs y estados de hallazgos de `api`.
- [PLAN.md](../PLAN.md): decisiones D1 a D3 y pendientes.
- `api/app/main.py`, `api/app/schemas.py`, `api/app/repository.py`: código verificado.
- `api/tests/test_api.py`: pruebas que documentan el comportamiento actual.
- Ejecución de rutas con `TestClient` sobre una base temporal, con `api/.venv`: los ejemplos marcados como verificados provienen de esa ejecución.
