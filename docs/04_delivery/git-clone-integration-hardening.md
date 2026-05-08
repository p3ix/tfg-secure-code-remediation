# Avance: integracion y hardening de `/analysis/git-clone`

## Objetivo del avance

Reforzar el flujo de clonado remoto para que gestione fallos de entorno y de red de forma controlada, con trazabilidad suficiente para diagnóstico, y dejar cobertura de pruebas sin dependencia de red real.

## Cambios implementados

### 1) Manejo robusto de errores en servicio de clonado

Archivo: `app/services/project_scan_service.py`

- Se captura `FileNotFoundError` al ejecutar `git clone` y se traduce a error funcional:
  - `"No se pudo ejecutar git clone: comando 'git' no disponible en PATH"`.
- Se mantiene timeout explícito con mensaje accionable:
  - `"git clone superó el tiempo límite (...)"`
- Se mantiene error controlado para retorno no cero de `git clone`.

### 2) Metadatos de diagnóstico ampliados

En la respuesta del flujo `git-clone` se añade información útil en `meta`:

- `git_command`
- `git_stdout_preview`
- `git_stderr_preview`

Esto permite investigar fallos sin volcar salidas completas ni romper el contrato principal.

### 3) Pruebas de integración simulada (sin red)

Archivo: `tests/test_project_scan_service.py`

Se añaden casos nuevos para `clone_and_analyze_repo`:

- éxito con `git clone` simulado;
- timeout de clonado;
- git no disponible en `PATH`;
- retorno no cero de `git clone`.

Además, se conserva la cobertura previa de endpoint `/analysis/git-clone`.

## Resultado de validación

Comandos ejecutados:

- `pytest -q tests/test_project_scan_service.py tests/test_runtime_analysis_service.py tests/test_dashboard.py tests/test_mvp_autofix_verification_endpoint.py`
- `pytest -q`

Resultado:

- tests del bloque ejecutados en verde;
- suite completa en verde: `125 passed`;
- cobertura global mantenida por encima del umbral del proyecto.

## Impacto

- Sin cambio de alcance funcional.
- Mayor resiliencia operativa de `git-clone`.
- Mejor trazabilidad para soporte y depuración.
- Menor riesgo de fallos silenciosos en entornos con herramientas incompletas.
