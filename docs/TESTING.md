# Testing

Registro de pruebas por componente. Cada ejecución indica componente e IDs de hallazgo (H-API-NN) de [HALLAZGOS.md](../HALLAZGOS.md).

## Componente api

### Comandos y resultados ejecutados

Directorio de ejecución: `api/` (raíz del componente). Intérprete: `api\.venv\Scripts\python.exe` (el Python del PATH no tiene FastAPI).

| # | Comando | Resultado | Código de salida | IDs |
|---|---|---|---|---|
| 1 | `python -m pytest --cov=app --cov-report=term-missing` (línea base, antes de agregar tests) | 22 passed | 0 | H-API-02, H-API-03, H-API-04 |
| 2 | `python -m pytest --cov=app --cov-report=term-missing` (con tests nuevos) | 42 passed, 4 xfailed, 0 failed | 0 | H-API-02, 03, 04, 05, 06, 09, 12 |
| 3 | `python -m pytest -p no:warnings --runxfail --tb=line` | 4 failed (esperado: los xfail reales fallan por la aserción de seguridad) | 1 | H-API-05, H-API-06 |

Nota: la salida de cobertura de la ejecución 2 corresponde a `app/`, con todas las sentencias cubiertas.

### Cobertura del código modificado

Método: `pytest-cov` con `--cov=app --cov-report=term-missing` desde `api/`. Medición por sentencias y ramas del paquete `app/`.

| Archivo | Numerador (cubiertas) | Denominador (sentencias) | Cobertura |
|---|---|---|---|
| `app/main.py` | 88 | 88 | 100% (ramas 8/8) |
| `app/repository.py` | 13 | 13 | 100% |
| `app/schemas.py` | 15 | 15 | 100% |
| **Modificado (main + repository + schemas)** | **116** | **116** | **100%** |

Cobertura global (`app/`, incluye `app/__init__.py` 0/0): 116/116 sentencias, 8/8 ramas, 100%. Se reporta por separado de la cobertura modificada, como exige el criterio. Verificado con `python -m coverage report --no-skip-covered` desde `api/`.

### Tabla de casos (endpoint | caso | tipo | resultado esperado)

Referencia de contrato: [ENDPOINTS.md](ENDPOINTS.md). Archivo de pruebas: `api/tests/test_api.py`.

#### GET /api/tasks

| Endpoint | Caso | Tipo | Resultado esperado |
|---|---|---|---|
| GET /api/tasks | Lista con token válido | Camino feliz | 200, lista de tareas (test existente) |
| GET /api/tasks | `owner=""` cae al usuario del token | Borde | 200, todas las tareas tienen `owner == "student"` |
| GET /api/tasks | Owner sin tareas | Borde | 200, `[]` |
| GET /api/tasks | Sin header `Authorization` | Error 401 | 401, `{"detail":"Invalid token: invalid token"}` |
| GET /api/tasks | Token inválido, expirado, mal formado, secreto incorrecto (tests existentes) | Error 401 | 401 |
| GET /api/tasks | Leer tareas de otro owner con `?owner=trainer` | Seguridad (IDOR) | **xfail** H-API-05: debe devolver 403 o no incluir la tarea de `trainer` |

#### POST /api/tasks

| Endpoint | Caso | Tipo | Resultado esperado |
|---|---|---|---|
| POST /api/tasks | Payload válido | Camino feliz | 201 (test existente) |
| POST /api/tasks | Payload `{}` | Borde | 201, defaults: `title=""`, `description=""`, `status=TODO`, `priority=MEDIUM`, `owner=student` |
| POST /api/tasks | `title=""` aceptado | Borde (caracterización, no aprobado) | 201, `title == ""`. Ver H-API-12 |
| POST /api/tasks | `owner: null` guardado como texto `"None"` | Borde (caracterización, no aprobado) | 201, `owner == "None"`. Ver pregunta abierta 3 en ENDPOINTS.md y H-API-05/12 |
| POST /api/tasks | Body no objeto (`["x"]`) | Error 422 | 422, `detail[0].loc == ["body"]` |
| POST /api/tasks | Sin header `Authorization` | Error 401 | 401 |
| POST /api/tasks | `owner: "trainer"` en el body | Seguridad (IDOR) | **xfail** H-API-05: no debe crear la tarea como `trainer` (403 o `owner == student`) |

#### GET /api/summary

| Endpoint | Caso | Tipo | Resultado esperado |
|---|---|---|---|
| GET /api/summary | Resumen válido | Camino feliz | 200, `{owner,total,byStatus,highPriorityOpen}` (test existente) |
| GET /api/summary | `owner=""` cae al usuario del token | Borde | 200, `owner == "student"`, `total == 2` |
| GET /api/summary | Sin header `Authorization` | Error 401 | 401 |
| GET /api/summary | Resumen de otro owner con `?owner=trainer` | Seguridad (IDOR) | **xfail** H-API-05: debe devolver 403 o `total == 0` para `trainer` |

#### POST /api/requirements

| Endpoint | Caso | Tipo | Resultado esperado |
|---|---|---|---|
| POST /api/requirements | Archivo `.txt` válido | Camino feliz | 201, `{owner,fileName,storedAt,size}` (test existente) |
| POST /api/requirements | Archivo sin extensión (`LEEME`) | Borde (caracterización) | 201, archivo guardado con contenido |
| POST /api/requirements | Archivo vacío | Borde | 201, `size == 0` |
| POST /api/requirements | 1 MiB | Borde (límite de tamaño) | 201, `size == 1048576`. Caracterización: no hay límite en el código. Pendiente de acuerdo |
| POST /api/requirements | Falta el campo `file` | Error 422 | 422, `detail[0].loc == ["body","file"]` |
| POST /api/requirements | Sin header `Authorization` | Error 401 | 401 |
| POST /api/requirements | Fallo al escribir (directorio con el mismo nombre) | Error 500 | 500, con `raise_server_exceptions=False` |
| POST /api/requirements | Nombre `../escape.txt` no escapa del directorio de subida | Seguridad (path traversal) | **xfail** H-API-06: `escape.txt` no debe existir fuera de la carpeta de subida |

#### GET /api/backend-health

| Endpoint | Caso | Tipo | Resultado esperado |
|---|---|---|---|
| GET /api/backend-health | Upstream responde 200 `{"status":"UP"}` | Camino feliz | 200, `{requestedBy:"student", status:200, body:'{"status":"UP"}'}` (servidor HTTP local) |
| GET /api/backend-health | Upstream responde 503 | Borde | 200, `status == 503` (se propaga) |
| GET /api/backend-health | Upstream inalcanzable | Error | 200, `status == 0`, `body` no vacío. Caracterización: el texto de la excepción llega al cliente (H-API-09) |
| GET /api/backend-health | Sin header `Authorization` | Error 401 | 401 |

### Fallos

Los 4 xfail son fallos reales conocidos, marcados `strict=True` (si un bug se corrige sin quitar el marcador, la suite falla). Con `--runxfail` los cuatro fallan con `AssertionError`, no con error de setup:

| Test | Hallazgo | Evidencia de fallo (`--runxfail`) |
|---|---|---|
| `test_list_denies_reading_another_owner_tasks` (api/tests/test_api.py:294) | H-API-05 | `'Trainer notes' not in ['Trainer notes']`: la lista de `trainer` se devuelve al token de `student` |
| `test_create_denies_writing_task_for_another_owner` (api/tests/test_api.py:348) | H-API-05 | `201 == 403 or 'trainer' == 'student'`: se crea la tarea con owner `trainer` |
| `test_summary_denies_reading_another_owner_summary` (api/tests/test_api.py:373) | H-API-05 | `200 == 403 or 1 == 0`: el resumen de `trainer` se devuelve |
| `test_upload_filename_cannot_escape_upload_dir` (api/tests/test_api.py:429) | H-API-06 | `assert not True`: `escape.txt` se escribe fuera del directorio de subida |

Estos bugs no se corrigieron en este paso, por lo que su estado en HALLAZGOS.md sigue en "Pendiente". No se adaptaron las aserciones para que pasen.

### Pendientes

- H-API-05 (IDOR, alta): requiere autorización ligada a la identidad del token. Depende de la coordinación con `auth/` (decisión D1 en PLAN.md).
- H-API-06 (path traversal, alta): `file.filename` sin normalizar (api/app/main.py:106). El xfail demuestra el fallo; aún no hay corrección.
- H-API-09 (fuga de detalle de error, media): el test de inalcanzable solo afirma que el body no está vacío; no fija el texto.
- H-API-12 (sin validación de payload, media): caracterización de `title=""` y `owner: null`. No aprobado como contrato.
- H-API-14 (broad except, baja): sin test propio.
- Pregunta abierta 3 y 5 de docs/ENDPOINTS.md (`owner: null`, límite de tamaño): esperan decisión humana.
- Dependencias de `auth/` para H-API-01: no probadas en este componente.

### Pruebas propuestas (no implementadas)

- Límite de tamaño de carga con 413 (pendiente de acuerdo con el equipo).
- Validación de `title` no vacío y rechazo de `owner: null` (H-API-12, tras aprobación).
- Cuando H-API-05 se corrija: quitar el xfail de los tres tests de IDOR.
