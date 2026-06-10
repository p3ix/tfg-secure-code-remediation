### Título

Pulido pre-release v0.1.0 (sin IA)

### Objetivo

Cerrar los últimos detalles de coherencia antes de publicar la primera release etiquetada
del proyecto (web operativa sin IA). No introduce funcionalidad: alinea la configuración de
ejemplo con las variables reales, elimina un enlace roto en la memoria y añade un historial
de cambios para acompañar la etiqueta `v0.1.0`.

### Tareas

- [x] Actualizar `.env.example` con las variables reales `TFG_*` (sin variables de IA).
- [x] Corregir el enlace roto de la memoria a `issue-traceability-index.md` creando el índice.
- [x] Crear `CHANGELOG.md` con la entrada de `v0.1.0`.
- [x] Verificar que no quedan enlaces internos rotos y que la suite sigue en verde.

### Criterio de cierre

- [x] `.env.example` refleja la superficie de configuración real del backend.
- [x] No hay enlaces internos rotos en `docs/07_memoria` ni en `README.md`.
- [x] `CHANGELOG.md` existe y describe la versión `v0.1.0`.
- [x] `ruff check` limpio y `pytest` en verde.

### Evidencias

- `.env.example`, `CHANGELOG.md`
- `docs/04_delivery/issue-traceability-index.md`
- `docs/07_memoria/01_evolucion_del_desarrollo.md` (enlace resuelto)
