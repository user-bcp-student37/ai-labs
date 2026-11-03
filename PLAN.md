# Plan de refactor

Documento compartido. Cada componente tiene su apartado. Este archivo describe propuestas;
no contiene cambios de código. Los estados viven en HALLAZGOS.md y no se modifican aquí.

## api

### Alcance

- Hallazgos del plan: H-API-01, H-API-02, H-API-03 y H-API-04 (estado Pendiente en HALLAZGOS.md).
- Fuera de este plan: H-API-05 (autorización por `owner` del cliente), H-API-06 (carga de archivos),
  H-API-07 y H-API-08 (SCA), H-API-09 a H-API-17. Se planean en pasos posteriores.
- Contrato a preservar: `docs/ENDPOINTS.md` no existe, así que se conserva el comportamiento observado
  en `api/app/main.py` (rutas, formas de respuesta y códigos 200/201/401 descritos en HALLAZGOS.md).
  No hay contrato acordado; cualquier cambio de respuesta requiere acuerdo humano.
- Convenciones: `docs/GOOD_PRACTICES.md` (sección api) y las reglas de clean code de `AGENTS.md`
  (una responsabilidad por función, sin duplicación, sin anidamiento profundo, sin números mágicos).

### Estructura objetivo mínima

Solo se crean los módulos necesarios para alojar los cuatro cambios. La separación completa de
capas queda para H-API-11.

| Archivo | Responsabilidad | Hallazgos |
|---|---|---|
| api/app/security.py (nuevo) | Extraer el token Bearer y verificar firma, expiración, emisor y audiencia | H-API-01 |
| api/app/repository.py (nuevo) | Consultas SQL parametrizadas sobre `tasks` | H-API-02, H-API-03, H-API-04 |
| api/app/schemas.py (nuevo) | Coerción de campos del body de alta con valores por defecto observados | H-API-03 |
| api/app/main.py | Solo `create_app` y registro de rutas; delega en los módulos anteriores | H-API-01 a H-API-04 |
| api/tests/test_api.py | Pruebas de caracterización antes de cada cambio | H-API-01 a H-API-04 |
| api/requirements.txt | Nueva dependencia de verificación de token (solo si se aprueba D1) | H-API-01 |

### Decisiones que requieren aprobación humana

Ninguna de estas decisiones está tomada. Se registran antes de implementar.

- **D1 — Formato del token (H-API-01).** `api/app/main.py:17-26` valida el token de `auth/`. Cambiar el
  formato rompe el flujo auth → api. Opciones:
  - A. Mantener Base64 y leer el secreto de una variable de entorno. Quita el secreto del código, pero el
    token sigue sin firma. No corrige el problema de fondo.
  - B. JWT firmado HS256 con la biblioteca PyJWT, secreto desde variable de entorno, con `exp`, `iss` y `aud`.
    Recomendada. Requiere dependencia nueva (justificación en H-API-01) y un cambio coordinado en `auth/`.
  - C. Firma HMAC propia con la biblioteca estándar. Evita la dependencia, pero reimplementa un estándar.
  - Pendiente: confirmar con el responsable de `auth/` el formato emitido. No se leyó `auth/`, por AMBITO.
- **D2 — Coerción en el alta (H-API-03).** `api/app/main.py:79-83` convierte todo con `str(...)`. Un número
  en `title` se acepta hoy. Un modelo Pydantic estricto devolvería 422 en ese caso. Propuesta: conservar la
  coerción en esta fase y mover la validación estricta a H-API-12.
- **D3 — Parámetro `owner` (H-API-02, H-API-04).** Este plan solo parametriza la consulta; no cambia quién
  puede pedir qué `owner`. La decisión sobre H-API-05 queda separada.

### Orden de ejecución propuesto

1. Confirmar el helper de token de las pruebas (ver "Punto a confirmar" abajo).
2. Escribir las pruebas de caracterización de la sección de cada hallazgo.
3. Implementar H-API-02, luego H-API-04, luego H-API-03 (todos usan `repository.py`).
4. Implementar H-API-01 al final, cuando D1 esté aprobada y `auth/` acordado.
5. Ejecutar la regresión completa después de cada hallazgo.

---

### H-API-01 — Token Base64 con secreto embebido

**Hallazgo (HALLAZGOS.md):** token Base64 con secreto embebido y sin firma. Severidad alta.

**Problema.** `api/app/main.py:14` define `LEGACY_SECRET = "WORKSHOP_SECRET_2026"` en el código.
`api/app/main.py:17-22` decodifica el token en Base64 y compara `parts[3]` con esa constante. Solo se valida
la expiración (`api/app/main.py:22`). Quien conozca el secreto puede fabricar un token con cualquier usuario
o rol. No hay firma, emisor ni audiencia.

**Cambio propuesto (opción B de D1).**
- Leer el secreto de `WORKSHOP_TOKEN_SECRET`. No definir un valor por defecto en el código. Si falta, la
  aplicación no arranca (fallo explícito en `create_app`).
- En `api/app/security.py`: funciones pequeñas con una sola responsabilidad:
  - `extract_bearer_token(header: str) -> str`: quita el prefijo `Bearer ` con validación explícita, sin
    `replace` sobre toda la cadena.
  - `decode_token(token: str, secret: str) -> dict`: verifica firma, `exp`, `iss` y `aud`.
  - `identity_from_claims(claims: dict) -> dict[str, str]`: devuelve `{"username", "role"}`, la misma forma
    que usan las rutas.
- `legacy_identity` se conserva como dependencia de FastAPI, pero solo encadena las funciones anteriores.
- Constantes con nombre para el emisor, la audiencia y los nombres de variables de entorno.
- El detalle de la excepción no va a la respuesta (se cubre en H-API-09; aquí se responde un mensaje fijo).

**Archivos a tocar.** `api/app/security.py` (nuevo), `api/app/main.py` (quitar `LEGACY_SECRET` y el cuerpo
de `legacy_identity`), `api/requirements.txt` (PyJWT fijada tras verificar versión y advisories),
`api/tests/test_api.py` (helper de token).

**Justificación de dependencia.** PyJWT verifica firma y claims estándar (`exp`, `iss`, `aud`) sin implementar
criptografía propia. Su versión y advisories se verifican antes de fijarla; no se incluye versión inventada.

**Pruebas de caracterización (antes de tocar).**
- Token válido con el formato actual → 200 en `GET /api/tasks`, con las tareas del usuario del token.
  Este caso documenta el comportamiento actual y dejará de ser válido tras D1; se marca como "cambia por D1".
- Token expirado → 401.
- Token con secreto distinto → 401.
- Token malformado (no Base64, o con menos de 4 campos) → 401.
- Sin cabecera `Authorization` → 401.
- Ya existente: `test_rejects_invalid_token` (api/tests/test_api.py:57).

**Criterio de aceptación.** Los cuatro casos de rechazo siguen devolviendo 401. El caso válido usa el
nuevo formato firmado con el secreto de prueba inyectado por variable de entorno. No se cambia la forma de
las respuestas.

**Dependencia externa.** Coordinar con `auth/` el emisor, la audiencia y la expiración. No se ejecuta
este hallazgo sin esa coordinación, porque el login y la api deben cambiar a la vez.

---

### H-API-02 — SQL concatenado en listado de tareas

**Hallazgo (HALLAZGOS.md):** `owner` se inserta en el texto de la consulta. Severidad alta.

**Problema.** `api/app/main.py:70` construye `WHERE owner='" + requested_owner + "'` por concatenación.
Un valor con comilla altera la sintaxis (la consulta falla o cambia el filtro).

**Cambio propuesto.** Mover la consulta a `api/app/repository.py` como función
`list_tasks_for_owner(connection, owner: str) -> list[sqlite3.Row]`. Usar `?` como marcador y pasar el
valor como parámetro. Conservar `ORDER BY id` y la lista de columnas en una constante con nombre
(`TASK_COLUMNS`), compartida con H-API-03. La ruta `list_tasks` solo resuelve el owner (`owner or identity`,
igual que hoy) y llama al repositorio.

**Archivos a tocar.** `api/app/repository.py` (nuevo), `api/app/main.py` (`list_tasks`, líneas 68-75).

**Pruebas de caracterización (antes de tocar).**
- Semilla: `student` tiene 2 tareas; `trainer` tiene 1. `GET /api/tasks` como `student` devuelve 2 y el orden
  por `id`.
- `GET /api/tasks?owner=trainer` como `student` devuelve 1 (comportamiento actual, cubierto por D3).
- Valor legítimo con comilla: `GET /api/tasks?owner=O'Brien` → esperado 200 con lista vacía. **Hoy falla**
  (la consulta concatenada rompe). Es una prueba roja que documenta el hallazgo; debe pasar después del cambio.

**Criterio de aceptación.** Los casos de caracterización de owner válido siguen igual. El caso con comilla
pasa. La consulta usa solo parámetros.

---

### H-API-03 — SQL concatenado en alta de tareas

**Hallazgo (HALLAZGOS.md):** campos del body concatenados en el INSERT. Severidad alta.

**Problema.** `api/app/main.py:84` concatena `title`, `description`, `status`, `owner` y `priority` en el
INSERT. `api/app/main.py:87` concatena `cursor.lastrowid` en el SELECT de relectura (es un entero, pero se
debe parametrizar igual).

**Cambio propuesto.**
- `api/app/repository.py`: `insert_task(connection, task: NewTask) -> int` con INSERT parametrizado; la
  fecha sigue siendo `datetime('now')` en el SQL (no es entrada del cliente).
  `get_task(connection, task_id: int) -> sqlite3.Row | None` con `WHERE id = ?`.
- `api/app/schemas.py`: `NewTask` (dataclass o modelo Pydantic simple) construido desde el body con la
  coerción observada (`str(...)`) y los mismos valores por defecto: `status="TODO"`, `priority="MEDIUM"`,
  `owner` = usuario del token (D2 y D3).
- Función `build_new_task(payload: dict, username: str) -> NewTask` con una sola responsabilidad.
  Sin anidamiento: los valores por defecto se toman con `payload.get(clave, defecto)` en una línea por campo.
- `api/app/main.py` (`create_task`) queda como: construir `NewTask`, insertar, leer, serializar.

**Archivos a tocar.** `api/app/repository.py`, `api/app/schemas.py` (nuevo), `api/app/main.py`
(`create_task`, líneas 77-88).

**Pruebas de caracterización (antes de tocar).**
- Alta mínima `{"title":"Add tests","description":"Improve coverage"}` → 201, `owner=student`,
  `status=TODO`, `priority=MEDIUM`. Verifica los defaults observados.
- Alta con `owner` explícito en el body → 201 con ese owner. Documenta el comportamiento de H-API-05;
  no se cambia en este plan.
- Alta con valor no textual (`"title": 123`) → 201 y `title="123"` (coerción D2).
- Alta con comilla legítima en `title` y en `description` (por ejemplo `Revisar el "login"`) → 201 y el
  texto guardado tal cual. **Hoy falla** (la consulta concatenada rompe). Prueba roja que debe pasar.
- Ya existente: `test_creates_task_and_summary` (api/tests/test_api.py) → 201 y `summary.total == 3`.

**Criterio de aceptación.** Los defaults y la coerción se mantienen. La forma de la respuesta no cambia.
El texto con comilla se guarda literal. Cero concatenación de entrada en SQL.

---

### H-API-04 — SQL concatenado en resumen

**Hallazgo (HALLAZGOS.md):** `owner` concatenado en el SELECT del resumen. Severidad alta.

**Problema.** `api/app/main.py:93` concatena `requested_owner` en `WHERE owner='...'`. Mismo patrón que H-API-02,
en otra ruta.

**Cambio propuesto.**
- `api/app/repository.py`: `list_status_and_priority(connection, owner: str) -> list[sqlite3.Row]` con `?`.
- Para aplicar clean code en la función que se toca, separar el conteo en `summarize_tasks(owner, rows) -> dict`
  con guard clauses. Es el mismo conteo de hoy; la reducción de condicionales completa queda en H-API-15
  y aquí solo se toca lo necesario.
- `api/app/main.py` (`summary`, líneas 90-105) queda como: resolver owner, consultar, resumir, devolver.

**Archivos a tocar.** `api/app/repository.py`, `api/app/main.py` (`summary`). Posible `api/app/summary.py`
si el conteo supera lo razonable en `repository.py`; decisión de implementación, no de plan.

**Pruebas de caracterización (antes de tocar).**
- `GET /api/summary` como `student` con semilla → `owner=student`, `total=2`,
  `byStatus={"TODO":1,"IN_PROGRESS":1}`, `highPriorityOpen=1` (la tarea "Refactor login" es HIGH y TODO).
- `GET /api/summary?owner=trainer` → `total=1`, `byStatus={"TODO":1}`, `highPriorityOpen=0`.
- Tras alta HIGH en TODO (test existente) → `highPriorityOpen` incrementa en 1.
- Owner con comilla legítima (`O'Brien`) → 200, `total=0`. **Hoy falla** (roja).
- Ya existente: `test_creates_task_and_summary`.

**Criterio de aceptación.** Los valores de respuesta son idénticos a la caracterización. Solo cambia la
forma de la consulta.

---

### Punto confirmado antes de las pruebas (resuelto)

- Resuelto: `api/tests/test_api.py` es válido. La salida de herramientas enmascara tokens `Bearer` como `******`; el baseline de 4 pruebas pasa con 200. Antes: `api/tests/test_api.py:16` define `headers()` con una cadena que aparece enmascarada en la lectura
  (`f"****** role)}"`). La línea 57 también usa `"******"`. Antes de escribir caracterización hay que
  confirmar en el archivo real que el helper genera `Bearer <token>`. No se afirma aquí su contenido exacto.

### Pruebas y cobertura

- Comando desde la raíz: `python tools/lab.py test api`. Desde `api/`: `python -m pytest` (configuración en
  `api/pyproject.toml`). **Resultado: no ejecutado.** Este plan no ejecutó pruebas.
- Las pruebas rojas listadas arriba se registran en `docs/TESTING.md` cuando se cree, con su estado real.
- Meta: 85% de cobertura del código modificado (método y numerador/denominador a registrar en
  `docs/TESTING.md`). Cobertura no medida todavía.

### Registro de ejecución

- H-API-02, H-API-03, H-API-04 (componente api): caracterización antes del cambio y corrección después.
  Antes: las pruebas de comilla e inyección fallaron (`OperationalError` y 3 filas en lugar de 0 en H-API-02;
  fallos equivalentes en H-API-03 y H-API-04). Después: `22 passed` con cwd `api/`
  (`.venv\Scripts\python.exe -m pytest --cov=app`), cobertura total 95%; `app/main.py` 94%.
- H-API-01: sin cambio de código. Se añadieron 4 pruebas de rechazo (token expirado, firma ajena, malformado,
  sin cabecera → 401) que pasan con el código actual; caracterizan el comportamiento observado. El cambio a
  PyJWT queda bloqueado por la coordinación con `auth/` (D1).
- Pendiente: lint no ejecutado; cobertura de `repository.py` y `schemas.py` no separada en el reporte.

### Pendientes

- Aprobación humana de D1, D2 y D3 y del orden de ejecución: **aprobado por el usuario** (mensaje: "aprobado"). Registrado en este documento; no se hizo ninguna otra decisión en su nombre.
- Helper de pruebas: resuelto (ver arriba). La salida de herramientas enmascara `******` en lugar del header `Bearer <token>`. No requiere cambio.
- Acuerdo con el responsable de `auth/` para H-API-01. Pendiente de coordinación externa.
- Verificación de versión y advisories de PyJWT antes de fijarla. Pendiente.
- `docs/ENDPOINTS.md` no existe: el contrato observado es la única referencia. Pendiente de crear.
- `docs/TESTING.md` y `PLAN.md` (este archivo) no existían antes de este paso; `docs/TESTING.md` sigue ausente.
