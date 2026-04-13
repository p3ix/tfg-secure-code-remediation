### Título

Implementar hoja de ruta inicial: ritual docs, higiene, análisis real, IA roadmap, memoria (#48)

### Objetivo

Materializar el plan «Hoja de ruta revisada (principio del TFG)»: documentación del ritual y fases, README y alcance actualizados, endpoints de análisis ZIP/Git, ADR de IA y capítulo de memoria sobre cadencia, sin editar el fichero `.cursor/plans/*.plan.md`.

### Tareas

- [x] `docs/01_roadmap_and_documentation_ritual.md` y sección en metodología
- [x] README, `docs/00_scope.md`, `pyproject.toml` + CI con `pip install -e ".[dev]"`
- [x] `app/services/project_scan_service.py`, rutas en `app/main.py`, `app/config.py`
- [x] ADR-002 IA, `GET /ai/status`, experimento `docs/03_experiments/real-project-scan-upload.md`
- [x] `docs/07_memoria/06_roadmap_fases_y_cadencia_memoria.md` y tests

### Criterio de cierre

- [x] `pytest` pasa con dependencias instaladas
- [x] OpenAPI lista `/analysis/upload-zip`, `/analysis/git-clone`, `/ai/status`

### Evidencias

- PR / commit; issue #48 cerrada
