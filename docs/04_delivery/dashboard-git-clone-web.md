# Avance: integración de `git_clone` en dashboard web

## Objetivo

Hacer usable desde `/dashboard` el análisis de repositorios Git HTTPS, evitando que el usuario dependa de `/docs` para lanzar este flujo.

## Cambios implementados

### Backend (`app/main.py`)

- Se amplía el contexto del dashboard con:
  - `git_clone_enabled`
  - `git_allowed_hosts`
- Se añade soporte del modo `analysis_mode == "git_clone"` en `dashboard_analyze`:
  - validación de feature flag (`TFG_ENABLE_GIT_CLONE`);
  - validación de URL no vacía;
  - ejecución vía `clone_and_analyze_repo`.

### Frontend (`app/templates/dashboard.html`)

- Nuevo modo visual: **Clonar repositorio Git**.
- Modo deshabilitable cuando `git_clone` está apagado en configuración.
- Nuevo campo de formulario: `git_url` (URL HTTPS del repositorio).
- Ayudas de UX con hosts permitidos visibles en la UI.

### Tests (`tests/test_dashboard.py`)

- Caso de éxito de análisis `git_clone` desde dashboard.
- Caso de error por URL vacía.
- Caso de error por `git_clone` desactivado en entorno.

## Validación

Comandos ejecutados:

- `.venv/bin/pytest -q tests/test_dashboard.py tests/test_project_scan_service.py`
- `.venv/bin/pytest -q`

Resultado:

- Suite completa en verde: `140 passed`
- Cobertura total: `91.49%`

## Conclusión

El dashboard ya soporta análisis por **ZIP, local-path y git-clone**, con validaciones y errores renderizados en web, cumpliendo el criterio de usar análisis Git sin pasar por `/docs`.
