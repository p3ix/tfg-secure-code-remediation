### Título

Diagnóstico Bandit/Semgrep visible en dashboard

### Objetivo

Mostrar en la consola web el estado de ejecución de Bandit y Semgrep (código de salida, hallazgos por herramienta, aviso si una no aportó filas) para que el usuario distinga un escaneo correcto sin findings de Semgrep de un fallo silencioso.

### Tareas

- [x] Propagar `tool_runs` del análisis interno a `scan.meta.tool_diagnostics` en presentable.
- [x] Renderizar panel de diagnóstico en `dashboard.html`.
- [x] Tests en `test_presentable_scan.py` y `test_dashboard.py`.
- [x] Documentar en `docs/04_delivery/` y nota en `docs/07_memoria/`.

### Criterio de cierre

- [x] Tras análisis runtime (ZIP/Git/local/fixtures runtime) el dashboard muestra estado Bandit y Semgrep.
- [x] Modo informes estáticos no muestra panel (sin `tool_runs`).
- [x] `pytest -q` en verde.

### Evidencias

- `app/services/presentable_scan.py`
- `app/templates/dashboard.html`
- `docs/04_delivery/diagnostico-herramientas-dashboard.md`
