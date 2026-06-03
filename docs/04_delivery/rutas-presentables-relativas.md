# Avance: rutas presentables relativas al origen

## Objetivo

Tras analizar un ZIP, un clon Git o una ruta local, Bandit y Semgrep suelen devolver `file_path` absoluto (p. ej. bajo `/tmp/tfg-unzip-...`). En el dashboard eso dificulta la lectura y la memoria del TFG. Esta iteración normaliza esas rutas a **relativas al directorio escaneado**.

## Cambios implementados

Archivo: `app/services/project_scan_service.py`

- `_presentable_file_path(file_path, analysis_root)`: si la ruta es absoluta y está bajo `analysis_root`, devuelve la ruta relativa con separadores POSIX (`src/test.py`). Si ya es relativa, se conserva. Si queda fuera de la raíz, se deja la ruta original (fallback seguro).
- `_relativize_findings_paths(findings, analysis_root)`: aplica la normalización in-place sobre `NormalizedFinding`.
- `analyze_directory`: tras `enrich_findings_with_classification`, se relativizan todos los hallazgos antes de serializar el payload.

Afecta a los tres flujos reales (ZIP, Git, local) porque todos pasan por `analyze_directory`.

## Pruebas

Archivo: `tests/test_project_scan_service.py`

- `test_presentable_file_path_relativizes_under_root`
- `test_presentable_file_path_keeps_already_relative`
- `test_presentable_file_path_keeps_path_outside_root`
- `test_relativize_findings_paths_updates_in_place`
- `test_analyze_directory_relativizes_finding_paths`

Comando: `.venv/bin/pytest -q tests/test_project_scan_service.py -k presentable or relativize`

## Resultado esperado en la web

Antes: `/tmp/tfg-unzip-1dxzbvi6/src/test/test.py:2`
Después: `src/test/test.py:2`

## Memoria

Nota breve en `docs/07_memoria/01_evolucion_del_desarrollo.md` (sección 10).
