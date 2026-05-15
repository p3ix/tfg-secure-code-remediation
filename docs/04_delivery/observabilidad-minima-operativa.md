# Avance: observabilidad mínima operativa

## Objetivo

Mejorar la trazabilidad de cada ejecución de análisis incorporando un identificador único (`analysis_id`) y eventos de logging por etapas del pipeline.

## Cambios implementados

### 1) `analysis_id` por ejecución

Archivo: `app/main.py`

- Se genera `analysis_id` por petición en endpoints de análisis y en `dashboard_analyze`.
- Se adjunta `analysis_id` a respuestas:
  - `POST /analysis/upload-zip`
  - `POST /analysis/git-clone`
  - `POST /analysis/local-path`
  - `POST /analysis/run-fixtures`
  - respuestas presentables asociadas a runtime/fixtures.
- El dashboard muestra `analysis_id` en la cabecera de resultados.

### 2) Logging estructurado por etapas

Archivo: `app/services/project_scan_service.py`

- Eventos de etapa:
  - `scan_start`
  - `bandit_done`
  - `semgrep_done`
  - `scan_parse_done`
  - `zip_extract_start` / `zip_extract_done`
  - `git_clone_start` / `git_clone_done`

Archivo: `app/services/runtime_analysis_service.py`

- Eventos de etapa en runtime fixtures:
  - `fixtures_runtime_start`
  - `fixtures_runtime_bandit_done`
  - `fixtures_runtime_semgrep_done`
  - `fixtures_runtime_parse_done`

### 3) Compatibilidad con tests y mocks

- Se añadieron wrappers para invocar funciones con `analysis_id` de forma opcional, evitando romper tests que monkeypatchean funciones con firmas antiguas.

## Pruebas y validación

Archivos de pruebas actualizados:

- `tests/test_project_scan_service.py`
- `tests/test_dashboard.py`
- `tests/test_run_fixtures_endpoint.py`

Comando de validación:

- `.venv/bin/pytest -q`

Resultado:

- `143 passed`
- cobertura global: `90.10%`

## Resultado

Cada análisis queda trazable con `analysis_id` visible para usuario y logs por etapa, mejorando diagnóstico operativo sin cambiar el alcance funcional del producto.
