### Título

Dashboard estable sin reports estáticos + trazabilidad clara dashboard/API

### Objetivo

Evitar que `GET /dashboard` falle con 500 cuando faltan reports del corpus MVP y dejar explícito, en documentación del TFG, qué flujos pasan por la consola web y cuáles quedan en endpoints API.

### Tareas
- [x] Ajustar `GET /dashboard` para renderizar HTML con estado vacío/aviso cuando falten reports estáticos.
- [x] Añadir mensaje de estado no bloqueante en plantilla para orientar a `fixture_runtime` o `upload_zip`.
- [x] Actualizar tests de dashboard: contrato 200 con mensaje en ausencia de reports.
- [x] Alinear documentación (`README`, experimento dashboard, memoria) con el flujo real dashboard/API.

### Criterio de cierre
- [x] En instalación sin `reports/bandit/*.json` y `reports/semgrep/*.json`, `/dashboard` responde `200` y muestra una guía de siguiente paso.
- [x] El comportamiento queda cubierto por `tests/test_dashboard.py`.
- [x] La documentación aclara que `POST /analysis/git-clone` y `GET /analysis/pipeline/mvp-autofix-verification` son endpoints API (no modo directo del formulario web).
- [x] Memoria con referencia cruzada al experimento del dashboard.

### Evidencias
- Código: `app/main.py`, `app/templates/dashboard.html`, `tests/test_dashboard.py`.
- Documentación: `README.md`, `docs/03_experiments/dashboard-web-analysis-console.md`, `docs/07_memoria/01_evolucion_del_desarrollo.md`.
- Verificación: `pytest -q`.
