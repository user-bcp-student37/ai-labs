---
name: api-unit-tests
description: "Diseña, crea y ejecuta pruebas unitarias para el API Python de este proyecto. Úsalo al cubrir lógica, repositorios o endpoints de FastAPI con pytest, SQLite temporal y TestClient."
---

# Skill: Pruebas unitarias para API

## 1) Metadata
- **Skill ID:** api-unit-tests
- **Version:** 0.1.0
- **Purpose:** Crear pruebas aisladas, legibles y verificables para el componente `api/`, preservando sus contratos y quality gates.
- **Audience (roles):** Backend, QA, Tech Lead
- **When to use:** Al agregar o corregir pruebas unitarias de la API Python, cubrir lógica existente o caracterizar comportamiento antes de refactorizar.
- **When NOT to use:** Para modificar `auth/` o `web/`, cambiar contratos sin aprobación, ejecutar pruebas contra servicios remotos o hacer una revisión de seguridad fuera del alcance de las pruebas solicitadas.
- **Sensitive inputs:** Usa datos ficticios, tokens de prueba aislados y recursos locales temporales. No incluyas credenciales, secretos reales, datos personales ni archivos reales.
- **Expected output:** Pruebas en `api/tests/`, resultado de las pruebas y resumen de cobertura relevante.

## 2) Inputs
Identifica:

- **Módulo, función o endpoint a probar:**
- **Comportamiento esperado y casos límite:**
- **Comportamiento actual:** (si se necesita una prueba de caracterización)
- **Contrato existente que debe preservarse:**
- **Restricciones:** (datos, dependencias, seguridad, archivos, servicios externos)

Si falta un resultado esperado, deriva el comportamiento solo del código y del contrato documentado. Señala la ambigüedad; no conviertas una hipótesis en un requisito.

## 3) Workflow
1. Trabaja desde la raíz de `ai-labs` y limita la inspección y los cambios al componente `api/` y a la documentación general necesaria.
2. Lee el código bajo prueba, `api/tests/test_api.py`, `api/pyproject.toml` y `tools/lab.py` para confirmar la implementación, los patrones y el comando vigente. No asumas que existe una ruta: verifica primero las rutas y dependencias implementadas.
3. Elige el nivel mínimo que comprueba el comportamiento:
   - **Lógica pura:** invoca directamente la función y verifica valores, bordes y errores.
   - **Repositorio:** usa una conexión SQLite local y aislada para verificar lectura, escritura, orden y parámetros.
   - **Ruta HTTP:** usa `TestClient` cuando debas validar método, ruta, autenticación, estado, cuerpo o serialización. Estas pruebas caracterizan la interfaz HTTP; no las presentes como unitarias puras.
4. Crea o amplía pruebas en `api/tests/`, siguiendo el estilo de pytest y los nombres descriptivos `test_<comportamiento>`.
5. Usa `tmp_path` para la base SQLite y archivos temporales. Crea la aplicación con `create_app(...)` cuando pruebes rutas y usa `TestClient` como context manager para cerrar recursos.
6. Prepara los datos por prueba; no dependas de la base `api/data/workshop.db`, del estado de otra prueba, del orden de ejecución ni de servicios externos.
7. Para dependencias externas, sustituye la interacción en su frontera con un mock o servidor local controlado. No hagas solicitudes a servicios reales.
8. Comprueba resultados observables y contratos relevantes: código HTTP, esquema y valores de respuesta, persistencia, aislamiento por identidad y errores esperados. Incluye entradas vacías, inválidas o con caracteres legítimos especiales cuando correspondan al caso.
9. Si la tarea incluye una refactorización, agrega primero pruebas de caracterización que capturen el comportamiento actual y conserva los contratos existentes. No cambies las rutas `/auth/login` o `/api/tasks` desde este componente; verifica en el código cuál es responsabilidad del API.
10. Ejecuta las pruebas dirigidas y luego el comando oficial del API descrito en Validation Rules. Informa fallos y cobertura sin ocultarlos ni reducir los quality gates.

## 4) Constraints
- Usa el stack ya configurado: Python, pytest, FastAPI, SQLite y `TestClient`; no agregues dependencias para escribir pruebas.
- Conserva endpoints, formatos de respuesta y comportamiento que consume el frontend. No inventes rutas o contratos.
- Mantén consultas SQL parametrizadas. Si una prueba comprueba entradas controladas por la petición, valida el resultado observable sin convertirla en una prueba de explotación.
- No uses credenciales reales, red, servicios compartidos ni la base de datos persistente del proyecto.
- No borres, debilites ni marques como aprobadas pruebas existentes `xfail` sin resolver y justificar el comportamiento asociado.
- No reduzcas umbrales de cobertura ni agregues exclusiones para hacer pasar las pruebas.
- Mantén cada prueba independiente, determinista y centrada en un comportamiento.
- No modifiques código de `auth/` o `web/`, ni hagas cambios de producción no requeridos para escribir las pruebas.

## 5) Validation Rules
La entrega es válida si:
- Las pruebas nuevas están en `api/tests/` y verifican comportamientos observables relevantes.
- El aislamiento local se mantiene mediante `tmp_path`, SQLite temporal y `TestClient` cuando corresponda.
- No se depende de servicios remotos, estado compartido ni datos reales.
- La ejecución dirigida termina correctamente; cualquier fallo se informa con su causa, sin ocultarlo.
- Se ejecuta desde la raíz:
  - `python tools/lab.py test api`
- El comando oficial mantiene `pytest-cov` y `--cov-fail-under=85`. Reporta el resultado real; no afirmes que se alcanzó el umbral si el comando falla.
- La cobertura del código modificado es al menos 85%, o se indica explícitamente qué falta y por qué.
- No se alteró el contrato de endpoints para acomodar la prueba.

## 6) Evidence
En la respuesta final, resume:
- Archivos de pruebas creados o modificados.
- Casos cubiertos y cualquier comportamiento ambiguo o caracterizado.
- Comando exacto ejecutado y su resultado.
- Resultado de cobertura y cualquier limitación pendiente.
