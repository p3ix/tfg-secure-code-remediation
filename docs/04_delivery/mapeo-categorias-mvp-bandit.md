# Avance: mapeo de categorías MVP Bandit (menos `unknown`)

## Problema observado

Al analizar un ZIP real con:

```python
import subprocess
subprocess.call("ls", shell=True)
```

Bandit emitía tres hallazgos, pero dos quedaban en categoría **`unknown`** (B404 import subprocess, B607 ruta parcial del ejecutable) porque el parser solo asignaba `subprocess_import_info` cuando la ruta contenía el segmento `command_injection/` del corpus MVP.

## Cambios implementados

Archivo: `app/services/parsers/bandit_parser.py`

| Regla Bandit | Categoría MVP | Remediación |
|--------------|---------------|-------------|
| B404 | `subprocess_import_info` | `detection_only` (siempre, sin depender de la ruta) |
| B607 | `subprocess_partial_path_info` (nueva) | `detection_only` |

Archivo: `app/services/findings_mapper.py`

- Clasificación CWE-78 / OWASP Injection para `subprocess_partial_path_info`, alineada con el contexto de subprocess.

Títulos presentables actualizados en Bandit y Semgrep parsers.

## Resultado esperado en dashboard

Resumen de categorías MVP para el mismo ZIP:

- `command_injection`: 1 (B602)
- `subprocess_import_info`: 1 (B404)
- `subprocess_partial_path_info`: 1 (B607)

Sin filas `unknown` para ese caso.

## Pruebas

- `tests/test_bandit_parser.py` — B404 en ruta real, B607
- `tests/test_findings_mapper.py` — clasificación de `subprocess_partial_path_info`

## Memoria

Nota en `docs/07_memoria/01_evolucion_del_desarrollo.md` (sección 11).
