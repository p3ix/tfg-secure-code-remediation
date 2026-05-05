### Titulo

Backlog de robustez A1-D2 por funcion mejorada

### Objetivo

Planificar y ejecutar una mejora integral de robustez del proyecto sin ampliar alcance funcional, asegurando que las funciones ya implementadas se comportan de forma correcta, estable y segura ante casos borde.

### Tareas
- [x] Definir issues granulares por funcion en API, seguridad operativa, pipeline y dashboard.
- [x] Ejecutar issue A1 (upload-zip): validaciones, contratos de error y tests.
- [x] Ejecutar issue A2 (git-clone): validaciones, timeouts y tests con mocks.
- [x] Ejecutar issue A3 (local-path): path-safety, errores consistentes y tests.
- [x] Ejecutar issue A4 (endpoints presentables): contrato estable y tests.
- [x] Ejecutar issue A5 (pipeline autofix verification): degradacion parcial robusta y tests.
- [x] Ejecutar issue B1 (hardening ZIP): traversal/zip bomb y tests.
- [x] Ejecutar issue B2 (subprocess analyzers): timeouts/fallos robustos y tests.
- [x] Ejecutar issue B3 (config entorno): validaciones de `TFG_*` y tests.
- [x] Ejecutar issue C1 (parser+mapper consistency): evitar ambiguedades y cubrir regresiones.
- [x] Ejecutar issue C2 (deduplicacion/agrupacion): idempotencia e invariantes con tests.
- [x] Ejecutar issue C3 (remediacion+verificacion): pruebas negativas y limites documentados.
- [x] Ejecutar issue D1 (formulario dashboard): validacion por modo y errores accionables.
- [x] Ejecutar issue D2 (render dashboard): estados vacios/parciales robustos con tests.
- [x] Actualizar documentacion de entrega y memoria con evidencias de robustez.

### Criterio de cierre
- [x] Todas las funciones actuales tienen al menos una mejora de robustez asociada y verificada con test.
- [x] Sin cambios de alcance funcional ni nuevas features fuera del MVP actual.
- [x] Suite de tests en verde tras los cambios.
- [x] Documentacion tecnica actualizada con decisiones, limites y evidencias.

### Evidencias
- Cambios en `app/main.py`, `app/config.py` y servicios de analisis/presentable/pipeline.
- Nuevos tests y ampliaciones en `tests/`.
- Documento de resultados: `docs/04_delivery/robustness-hardening-report.md`.
- Resultado de test: `121 passed`, cobertura `87.76%` (`.venv/bin/pytest -q`).
