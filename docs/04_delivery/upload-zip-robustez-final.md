# Avance: robustez final de `POST /analysis/upload-zip`

## Objetivo

Reforzar el endpoint de subida ZIP para evitar falsos positivos de tipo de fichero y garantizar errores consistentes cuando el contenido recibido no corresponde a un ZIP válido.

## Cambios implementados

Archivo: `app/main.py`

- Se añadió validación explícita de tipos MIME permitidos para subida ZIP:
  - `application/zip`
  - `application/x-zip-compressed`
  - `application/octet-stream`
- Se añadió validación de firma ZIP mínima (`PK...`) antes de invocar el análisis.
- Se aplicó el mismo criterio al flujo del dashboard (`/dashboard/analyze`, modo `upload_zip`) para mantener consistencia API/UI.

## Pruebas añadidas/actualizadas

- `tests/test_project_scan_service.py`
  - rechazo por `content_type` no permitido;
  - rechazo por firma ZIP inválida;
  - ajustes en tests mockeados para usar contenido con firma válida.
- `tests/test_dashboard.py`
  - rechazo en UI cuando el contenido no tiene firma ZIP válida.

## Validación

Comando ejecutado:

- `.venv/bin/pytest -q`

Resultado:

- `137 passed`
- cobertura total: `91.44%`

## Conclusión

El endpoint mantiene su funcionalidad, pero ahora distingue mejor entre archivo nombrado como ZIP y contenido realmente ZIP, reduciendo errores silenciosos y comportamientos ambiguos.
