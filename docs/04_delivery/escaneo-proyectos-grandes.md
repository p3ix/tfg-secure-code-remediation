# Avance: escaneo robusto de proyectos grandes

## Objetivo

Evitar bloqueos y tiempos excesivos en análisis de árboles grandes mediante una validación previa de tamaño antes de ejecutar Bandit y Semgrep.

## Cambios implementados

### Configuración (`app/config.py`)

Se añadieron nuevos límites configurables:

- `TFG_ANALYSIS_MAX_FILES` (por defecto `20000`)
- `TFG_ANALYSIS_MAX_BYTES` (por defecto `314572800`, ~300 MB)

### Servicio de escaneo (`app/services/project_scan_service.py`)

- Nueva validación previa `_validate_analysis_tree_size(...)` en `analyze_directory`.
- Corte temprano con error accionable si se supera:
  - límite de número de ficheros;
  - límite de tamaño total en bytes.
- Mensajes incluyen variable de entorno a ajustar para facilitar operación.

## Pruebas añadidas

Archivo: `tests/test_project_scan_service.py`

- rechazo por exceso de número de ficheros;
- rechazo por exceso de bytes totales.

## Validación

Comando ejecutado:

- `.venv/bin/pytest -q`

Resultado:

- `143 passed`
- cobertura global: `90.71%`

## Conclusión

El flujo de análisis mantiene funcionalidad, pero ahora evita ejecuciones inviables en proyectos grandes con errores claros y configurables.
