# Avance: contrato unificado de errores (API + dashboard)

## Objetivo

Unificar el tratamiento de errores para los flujos de análisis, de forma que:

- la API devuelva estructura estable en `detail`;
- el dashboard renderice mensajes alineados con el mismo `error_code`.

## Cambios implementados

Archivo: `app/main.py`

- Se añade mapeo centralizado de excepciones:
  - `_map_analysis_error(exc, analysis_mode)` -> `(status_code, error_code, message)`
- Se añade constructor de payload:
  - `_error_detail(error_code, message)` -> `{"error_code": "...", "message": "..."}`
- Endpoints API adaptados:
  - `POST /analysis/upload-zip`
  - `POST /analysis/git-clone`
  - `POST /analysis/local-path`
- `dashboard_analyze` adaptado para mostrar error con prefijo de código:
  - formato: `[ERROR_CODE] message`

## Contrato API aplicado

Para endpoints de análisis, los errores siguen este formato:

```json
{
  "detail": {
    "error_code": "ZIP_INVALID_SIGNATURE",
    "message": "El contenido subido no tiene firma ZIP válida"
  }
}
```

## Tabla resumida de códigos

- `ZIP_EMPTY_CONTENT` -> 400
- `ZIP_EXTENSION_REQUIRED` -> 400
- `ZIP_CONTENT_TYPE_INVALID` -> 400
- `ZIP_INVALID_SIGNATURE` -> 400
- `ZIP_TOO_LARGE` -> 413
- `GIT_CLONE_DISABLED` -> 403
- `GIT_URL_REQUIRED` -> 400
- `GIT_URL_INVALID` -> 400
- `GIT_HOST_NOT_ALLOWED` -> 400
- `GIT_BINARY_MISSING` -> 502
- `GIT_CLONE_TIMEOUT` -> 502
- `GIT_CLONE_FAILED` -> 502
- `LOCAL_PATH_DISABLED` -> 403
- `LOCAL_PATH_INVALID` -> 400
- `LOCAL_PATH_NOT_FOUND` -> 404
- `ANALYZER_TIMEOUT` -> 502
- `ANALYZER_REPORT_MISSING` -> 502
- fallback:
  - `ANALYSIS_BAD_REQUEST` -> 400
  - `ANALYSIS_RUNTIME_ERROR` -> 502
  - `ANALYSIS_INTERNAL_ERROR` -> 500

## Pruebas y validación

Archivos actualizados:

- `tests/test_project_scan_service.py`
- `tests/test_dashboard.py`

Comandos ejecutados:

- `.venv/bin/pytest -q tests/test_project_scan_service.py tests/test_dashboard.py`
- `.venv/bin/pytest -q`

Resultado:

- suite completa en verde: `141 passed`
- cobertura global: `90.82%`

## Conclusión

Se elimina la ambigüedad entre errores API y visualización web, dejando un contrato reproducible para cliente y para dashboard con códigos estables.
