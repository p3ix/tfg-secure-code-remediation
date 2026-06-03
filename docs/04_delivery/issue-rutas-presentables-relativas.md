### Título

Rutas presentables relativas al origen del análisis

### Objetivo

Evitar que el dashboard muestre rutas absolutas del servidor (p. ej. `/tmp/tfg-unzip-.../src/test.py`) tras analizar ZIP, Git o ruta local; mostrar rutas relativas al directorio escaneado.

### Tareas

- [x] Añadir normalización de `file_path` en `analyze_directory` tras enriquecer hallazgos.
- [x] Añadir tests unitarios para rutas absolutas, relativas y fuera de la raíz.
- [x] Documentar el avance en `docs/04_delivery/`.
- [x] Actualizar brevemente `docs/07_memoria/01_evolucion_del_desarrollo.md`.

### Criterio de cierre

- [x] Hallazgos de escaneo real usan `file_path` relativo al `target` cuando la ruta está bajo esa raíz.
- [x] La suite de tests permanece en verde.
- [x] Existe documentación de entrega de la iteración.

### Evidencias

- `app/services/project_scan_service.py`
- `tests/test_project_scan_service.py`
- `docs/04_delivery/rutas-presentables-relativas.md`
