CONTEXTO
Estás en la raíz de ai-labs. HALLAZGOS.md es la matriz de hallazgos del Día 1.

OBJETIVO
Generar HU-01.md en la raíz de ai-labs a partir de las filas "Pendiente"
de HALLAZGOS.md relacionadas con el token de autenticacion.

RESTRICCIONES
No inventes hallazgos que no esten en HALLAZGOS.md. No incluyas valores de
tokens, secretos ni credenciales.

CRITERIOS DE ACEPTACION
La evidencia identifica el componente y sus IDs H-AUTH-NN, H-API-NN o H-WEB-NN.
HU-01.md tiene las secciones Origen, Contexto, Ajustes necesarios, Criterios de
aceptacion y Evidencia esperada. Origen lista los Id (H-AUTH-NN, H-API-NN o H-WEB-NN) y la evidencia
archivo:linea de cada hallazgo usado. Cada criterio de aceptacion es
verificable con una prueba.

FORMATO DE RESPUESTA
Solo el archivo HU-01.md.

## web

### H-WEB-01 — Dependencia Axios directa marcada con vulnerabilidades de severidad alta
- Estado: CANDIDATO
- Evidencia: `web/package.json:19` fija `axios` en `0.31.0`. `npm audit --json` ejecutado desde `web/` reporta 43 vulnerabilidades en el árbol (27 moderadas, 10 altas y 6 críticas) y marca Axios como dependencia directa de severidad alta, con avisos que incluyen contaminación de prototipos y bypass de autenticación.
- Impacto: la biblioteca se usa en las solicitudes de autenticación y tareas; la exposición concreta depende de las condiciones de cada aviso y no queda demostrada solo con este análisis.
- Prioridad propuesta: Alta
- Contrato potencialmente afectado: `POST /auth/login` y `GET /api/tasks`, por ser los flujos que usan Axios.
- Cómo validarlo: revisar los avisos de `npm audit --json` individualmente para confirmar aplicabilidad al uso del cliente; actualizar a una versión corregida compatible, ejecutar `npm audit` y pruebas de login/carga de tareas.

### H-WEB-02 — La sesión persistida puede romper la inicialización del dashboard
- Estado: CANDIDATO
- Evidencia: `web/src/app/login/login.component.ts:46-49` acepta la respuesta si contiene `token` y persiste `response.data.user` sin validarlo. `web/src/app/dashboard/dashboard.component.ts:36-37` ejecuta `JSON.parse` sobre `workshop_user` antes del bloque `try` que maneja errores de carga.
- Impacto: si la respuesta carece de `user` o el valor guardado no es JSON válido, la navegación puede dejar el dashboard sin estado de recuperación controlado antes de solicitar tareas.
- Prioridad propuesta: Media
- Contrato potencialmente afectado: forma de respuesta de `POST /auth/login` y sesión local usada por `/dashboard`.
- Cómo validarlo: probar una respuesta con token y sin `user`, además de un `workshop_user` corrupto; comprobar que no se persista una sesión incompleta y que el dashboard recupere o informe el estado sin fallar durante su inicialización.

### H-WEB-03 — El nombre de usuario se concatena sin codificar en la consulta de tareas
- Estado: CANDIDATO
- Evidencia: `web/src/app/dashboard/dashboard.component.ts:43` concatena `this.user.username` directamente en `?owner=`.
- Impacto: si se permite un nombre con caracteres reservados de URL, por ejemplo `&` o `#`, la consulta puede interpretarse con otro parámetro o truncarse y mostrar una lista incorrecta.
- Prioridad propuesta: Media
- Contrato potencialmente afectado: `GET /api/tasks?owner=...`.
- Cómo validarlo: con un nombre de usuario que contenga caracteres reservados, inspeccionar la URL enviada y verificar que el servidor reciba el valor completo como un solo parámetro `owner`.

### H-WEB-04 — El comparador de prioridades no contempla valores iguales
- Estado: CANDIDATO
- Evidencia: `web/src/app/dashboard/dashboard.component.ts:54` devuelve `1` cuando `a.priority` no es mayor que `b.priority`, incluso si ambas prioridades son iguales.
- Impacto: el comparador no define correctamente la igualdad y el orden relativo de tareas con la misma prioridad puede no conservarse de forma fiable.
- Prioridad propuesta: Baja
- Contrato potencialmente afectado: orden de presentación de tareas en el dashboard.
- Cómo validarlo: probar la ordenación con varias tareas de igual prioridad y verificar el orden esperado; el comparador debe devolver `0` para prioridades iguales.