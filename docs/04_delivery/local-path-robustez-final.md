# Avance: robustez final de `POST /analysis/local-path`

## Objetivo

Endurecer la resolución de rutas locales para evitar configuraciones inválidas y entradas ambiguas en el análisis por ruta relativa bajo `TFG_LOCAL_ANALYSIS_ROOT`.

## Cambios implementados

Archivo: `app/services/project_scan_service.py`

- Se valida que `allowed_root` exista y sea directorio antes de resolver rutas.
- Se rechaza el uso de separador `\\` en `relative_path` para evitar ambigüedades de plataforma.
- Se normaliza `analysis_target` en `analyze_local_path_relative` con ruta relativa resuelta (no texto bruto de entrada).

## Pruebas añadidas

Archivo: `tests/test_local_path_hardening.py`

- raíz permitida inexistente o inválida;
- ruta relativa con separador `\\`;
- normalización de etiqueta `analysis_target` en flujo local-path.

Además, se mantiene cobertura de casos previos en `tests/test_project_scan_service.py`.

## Validación

Comando ejecutado:

- `.venv/bin/pytest -q`

Resultado:

- `137 passed`
- cobertura total: `91.44%`

## Conclusión

El flujo `local-path` mantiene alcance funcional, pero reduce superficie de errores por configuración o formato de ruta, mejorando la predictibilidad del endpoint.
