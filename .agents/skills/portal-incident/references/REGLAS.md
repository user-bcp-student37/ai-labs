# Reglas para preparar y registrar incidencias

## Evidencia

- Usa únicamente hechos encontrados en el log del caso y las referencias que
  este incluya.
- Conserva el estado del hallazgo (`CANDIDATO`, `Pendiente`, `Aprobado` u otro
  estado de origen) y distingue hechos de hipótesis.
- No conviertas una prioridad propuesta en severidad confirmada.
- Cada evidencia debe apuntar a una fuente verificable. Si no se puede verificar
  con el material disponible, indícala como pendiente y no la completes por
  inferencia.

## Minimización de datos

- Excluye tokens, contraseñas, secretos, cookies, cabeceras de autenticación,
  datos personales, identificadores de clientes y contenido bancario.
- No incluyas dumps o logs completos cuando baste un extracto mínimo.
- Si la evidencia necesaria contiene datos sensibles, reemplázalos por
  `[REDACTADO]`; no intentes reconstruirlos.
- No guardes credenciales del portal en archivos del repositorio.

## Revisión y registro

- El archivo `incidencia.json` es un borrador hasta que una persona revise y
  apruebe explícitamente su contenido.
- No se registra una incidencia con datos requeridos ausentes, evidencia
  contradictoria o un hallazgo no aprobado para registro.
- El único envío permitido es mediante `registrar_incidencia` del MCP del
  portal, tras aprobación explícita.
- Después del registro, confirma el identificador con `consultar_incidencia`.
- Si el registro o la consulta falla, reporta el fallo; no declares éxito ni
  repitas el registro automáticamente.
- Si el MCP del portal no está conectado o su contrato no coincide con
  `CONTRATO.json`, detente y solicita validación del responsable del portal.

## Fuera de alcance

- No construir ni ejecutar el servidor MCP.
- No implementar endpoints o lógica de una API bancaria.
- No crear issues, pull requests, commits ni subir archivos a GitHub.

