# Avance: dashboard web en modo real-first

## Objetivo

Reorientar la pantalla principal para priorizar análisis reales (ZIP, Git y ruta local), manteniendo los flujos de fixtures como soporte secundario de demo/MVP.

## Cambios implementados

Archivo: `app/templates/dashboard.html`

- Reordenación de modos en el formulario de análisis:
  1. `upload_zip` (real)
  2. `git_clone` (real)
  3. `local_path` (real)
  4. `fixture_reports` (MVP/demo)
  5. `fixture_runtime` (MVP/demo)
- Etiquetado explícito por contexto:
  - `"real"` para uso productivo del análisis.
  - `"MVP/demo"` para corpus interno de validación.
- Ajustes de copy en cabecera y metadatos para guiar al usuario hacia flujos reales.

Archivo: `tests/test_dashboard.py`

- Validación de presencia de etiquetas y modos real-first en el render principal.

## Validación

Comandos ejecutados:

- `.venv/bin/pytest -q tests/test_dashboard.py`
- `.venv/bin/pytest -q`

Resultados:

- tests en verde;
- suite completa: `140 passed`;
- cobertura global: `91.49%`.

## Conclusión

El dashboard queda orientado al uso real sin romper compatibilidad con modos de demo. Un usuario nuevo puede empezar por ZIP/Git/local-path sin conocer los fixtures del MVP.
