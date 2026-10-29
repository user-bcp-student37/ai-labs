## 1. Caracterización (sin cambios de producción)

- [x] 1.1 Añadir pruebas de login válido de `student` y `trainer` que verifiquen 200, `user` (`username`, `displayName`, `role`), `token`, `expiresIn` = 3600 y `debug` = `authenticated-with-legacy-flow`.
- [x] 1.2 Añadir pruebas de 401 con credenciales incorrectas y con usuario inexistente, verificando el mensaje actual `Invalid user <u> or password`.
- [x] 1.3 Verificar que las validaciones 400 (request nulo, usuario vacío, contraseña vacía), 405, 406 y 415 siguen igual. Solo se añaden pruebas que faltan.
- [x] 1.4 Añadir prueba de migración de `LegacyFixture123!`: el valor cambia a hash y el login original responde 200.
- [x] 1.5 Añadir prueba de segunda ejecución de `migratePlaintextPasswords` que confirme que el valor almacenado no cambia.
- [x] 1.6 Añadir prueba de `seedUserIfMissing`: no duplica usuarios existentes y guarda hash, no texto plano.
- [ ] 1.7 Ejecutar `python tools/lab.py test auth` y registrar resultados observados. Todas las pruebas de esta sección deben estar en verde antes de seguir.

## 2. Línea base del comportamiento actual de arranque

- [x] 2.1 Registrar como evidencia (no como aserción de resultado deseado) que un fallo en `initialize()` hoy solo imprime la traza y no detiene el servicio.
- [x] 2.2 Confirmar con una prueba o evidencia observada que `LegacyDatabase.initialize()` se ejecuta en el primer uso del bean y no al arrancar.
- [x] 2.3 Documentar el resultado de 2.1 y 2.2 en la nota de evidencia del cambio antes de modificar producción.

## 3. Regresión de clasificación de contraseñas

- [x] 3.1 Añadir prueba de texto plano `$2a$10$...` que se migra, cambia su valor almacenado y autentica con la contraseña original.
- [x] 3.2 Añadir pruebas equivalentes para prefijos `$2b$` y `$2y$`.
- [x] 3.3 Añadir prueba de `$pbkdf2-sha256$` malformado (formato incompleto) que se trata como texto plano y se migra.
- [x] 3.4 Añadir prueba de hash válido de `PasswordHasher` que no se modifica durante la migración.
- [ ] 3.5 Ejecutar `python tools/lab.py test auth`; las pruebas nuevas deben pasar sin cambiar producción.

## 4. Propagación de fallos de inicialización

- [x] 4.1 Cambiar `LegacyDatabase.initialize()` para dejar de capturar `Exception` y propagar una excepción no comprobada con causa original (por ejemplo `IllegalStateException`).
- [x] 4.2 Eliminar el `printStackTrace()` del camino de fallo sustituido por la propagación.
- [x] 4.3 Ejecutar las pruebas de las secciones 1 y 3; deben seguir en verde.

## 5. Inicialización eager y pruebas de arranque

- [x] 5.1 Solo si 2.2 confirma arranque perezoso: activar la inicialización en el arranque con `@Startup` de Quarkus o un observador de `StartupEvent`.
- [x] 5.2 Añadir prueba de fallo de arranque en proceso o perfil separado con `AUTH_DB_URL` apuntando a una ruta no accesible. Verificar que el arranque falla con error observable y que `POST /auth/login` no responde.
- [x] 5.3 Añadir prueba de fallo de migración (excepción en `migratePlaintextPasswords`) que impida el arranque.
- [ ] 5.4 Ejecutar `python tools/lab.py test auth` y registrar resultados reales.

## 6. Validación final y cierre

- [x] 6.1 Confirmar que el contrato de `POST /auth/login` y `GET /q/health` no cambió frente a la línea base de la sección 1.
- [ ] 6.2 Confirmar que las consultas siguen parametrizadas en `LegacyDatabase`.
- [x] 6.3 Verificar cobertura del código modificado igual o superior a 85%.
- [ ] 6.4 Ejecutar `python tools/lab.py test auth` completo y registrar el resultado observado. Hasta entonces la validación figura como **No ejecutado**.
- [ ] 6.5 Revisar que no se modificó nada fuera de `auth/` ni de `openspec/changes/secure-legacy-password-migration/`.

## Fuera de esta lista

- Documentar en la guía de ejecución que un `AUTH_DB_URL` inválido impide el arranque (design.md lo menciona). Requiere aprobación antes de hacerlo.
- Confirmar el criterio BCrypt frente a PBKDF2 y las líneas de HU-01 desactualizadas con el equipo antes de la sección 3.
