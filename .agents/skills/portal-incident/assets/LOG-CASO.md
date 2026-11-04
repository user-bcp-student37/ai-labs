# Log del caso (evidencia documental anonimizada)

> Ejemplo de entrada construido a partir de la documentación disponible en este
> repositorio. No es telemetría de producción ni un registro generado por una
> ejecución real.

- Hallazgo: `H-WEB-02`
- Componente: `web`
- Estado en `HALLAZGOS.md`: `CANDIDATO`
- Prioridad propuesta en la matriz: `Media`
- Fuente de contexto: `docs/H-WEB-02-spec.md`

## Evidencia registrada

1. `web/src/app/login/login.component.ts:46-49`: el hallazgo documenta que la
   respuesta se acepta al contener un token y que `response.data.user` se
   persiste sin validación previa.
2. `web/src/app/dashboard/dashboard.component.ts:36-37`: el hallazgo documenta
   que `JSON.parse` se ejecuta sobre `workshop_user` antes del bloque que
   captura errores de carga.
3. Impacto potencial documentado: una respuesta sin usuario o un valor local
   inválido puede interrumpir la inicialización del dashboard sin recuperación
   controlada.

## Validación propuesta en la fuente

- Probar login con token y usuario ausente; verificar que no se guarde una
  sesión parcial.
- Probar usuario persistido ausente o JSON inválido; verificar recuperación
  controlada y redirección a login.
- Mantener una sesión válida y verificar la carga existente de tareas.

## Límites de esta entrada

- No contiene nombres de usuario, tokens, contraseñas, secretos ni datos de
  clientes.
- No afirma que las pruebas hayan sido ejecutadas ni que el hallazgo haya
  recibido aprobación para registrarse en el portal.
- La matriz mantiene el estado `CANDIDATO`; requiere decisión humana antes de
  cualquier registro.

