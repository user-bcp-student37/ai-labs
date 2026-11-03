# Recuperación ante una sesión local inválida en el dashboard

## Fuente

Hallazgo aprobado: **H-WEB-02 — La sesión persistida puede romper la inicialización del dashboard**.

- Evidencia: [`web/src/app/login/login.component.ts:46-49`](../web/src/app/login/login.component.ts) guarda `response.data.user` después de comprobar únicamente que la respuesta contiene un token.
- Evidencia: [`web/src/app/dashboard/dashboard.component.ts:36-37`](../web/src/app/dashboard/dashboard.component.ts) ejecuta `JSON.parse` sobre `workshop_user` antes del bloque que captura errores de carga.
- Impacto: una respuesta sin usuario o un valor local inválido puede interrumpir la inicialización del dashboard sin recuperación controlada.

## Contexto actual

Tras recibir un token, el login persiste el usuario y navega al dashboard. El dashboard lee el token y analiza el usuario guardado antes de solicitar tareas. Si el usuario no existe o no contiene JSON válido, el error ocurre antes del manejo de errores de la solicitud.

## Problema confirmado

El flujo permite guardar una sesión incompleta y no maneja el fallo al recuperar el usuario persistido. En esas condiciones, el dashboard puede no completar su inicialización ni guiar al usuario para recuperar la sesión.

## Comportamiento a preservar

- Mantener `POST /auth/login` y su contrato de respuesta existente.
- Con una respuesta válida, persistir la sesión y navegar al dashboard como hasta ahora.
- Con una sesión válida, mantener la carga de tareas desde `GET /api/tasks` y el comportamiento actual del dashboard.
- Mantener el cierre de sesión existente, que elimina el token y el usuario y vuelve a `/login`.

## Alcance

- Evitar que una respuesta de login sin los datos de usuario requeridos establezca una sesión parcial.
- Recuperar de forma controlada una sesión cuyo usuario guardado esté ausente o no pueda analizarse: limpiar token y usuario y redirigir a `/login`.
- Mostrar un error controlado durante el login si la respuesta no permite establecer una sesión válida.
- Cubrir los flujos de sesión válida e inválida con pruebas.

## Fuera de alcance

- Cambiar los endpoints o el formato de respuesta de autenticación o tareas.
- Cambiar almacenamiento, expiración o renovación del token.
- Modificar autorización del backend o el contenido funcional del dashboard.
- Rediseñar la interfaz de login o dashboard.

## Criterios de aceptación

1. Dada una respuesta válida de `POST /auth/login`, el token y el usuario se persisten, y la aplicación navega al dashboard.
2. Dada una respuesta con token pero sin usuario, el login no persiste una sesión parcial ni navega al dashboard y presenta un error controlado.
3. Dado un `workshop_user` ausente o con contenido JSON inválido al abrir el dashboard, la aplicación elimina `workshop_token` y `workshop_user` y redirige a `/login`, sin lanzar un error no controlado.
4. Dada una sesión válida, el dashboard continúa solicitando `GET /api/tasks` con el token de autorización y presenta las tareas conforme al comportamiento actual.
5. Las pruebas automatizadas verifican los cuatro casos anteriores, incluyendo que no se soliciten tareas antes de validar la sesión.

## Contratos afectados/protegidos

- **Protegido:** `POST /auth/login`; no se cambia el endpoint ni el formato existente.
- **Protegido:** `GET /api/tasks`; no se cambia el endpoint, la forma de la solicitud ni el formato de respuesta esperado.
- **Flujo local:** `workshop_token` y `workshop_user` deben representar una sesión utilizable conjuntamente.
- **Supuesto para validar:** `user.username` es necesario para la consulta de tareas; `user.displayName` puede faltar porque la interfaz ya usa `username` como alternativa de presentación.

## Riesgos, supuestos y preguntas abiertas

- La spec asume que una sesión sin usuario no es válida, aun cuando la respuesta incluya un token.
- La recuperación acordada elimina el token junto con el usuario inválido; esto obliga al usuario a autenticarse de nuevo.
- La forma mínima aceptada para el usuario debe concordar con el contrato real de `POST /auth/login`; confirmar que `username` es obligatorio y si existen otros campos requeridos antes de implementar.
