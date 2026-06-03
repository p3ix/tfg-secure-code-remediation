### Título

Ampliar mapeo de categorías MVP en Bandit (menos `unknown`)

### Objetivo

Reducir hallazgos `unknown` en escaneos reales (ZIP/Git/local) mapeando reglas Bandit frecuentes de subprocess (`B404`, `B607`) a categorías MVP con título y remediación coherentes, no solo cuando la ruta contiene `command_injection/` del corpus fixtures.

### Tareas

- [x] Mapear `B404` → `subprocess_import_info` sin condicionar por ruta del fixture.
- [x] Mapear `B607` → nueva categoría `subprocess_partial_path_info` (informativo).
- [x] Añadir clasificación CWE/OWASP en `findings_mapper.py`.
- [x] Tests en `test_bandit_parser.py` y `test_findings_mapper.py`.
- [x] Documentar en `docs/04_delivery/` y nota en `docs/07_memoria/`.

### Criterio de cierre

- [x] Un ZIP con `import subprocess` + `shell=True` ya no muestra categorías `unknown` para B404/B607.
- [x] `pytest -q` en verde.
- [x] Documentación de entrega actualizada.

### Evidencias

- `app/services/parsers/bandit_parser.py`
- `app/services/findings_mapper.py`
- `docs/04_delivery/mapeo-categorias-mvp-bandit.md`
