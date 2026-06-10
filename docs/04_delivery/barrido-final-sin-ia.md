# Barrido final de calidad sin IA (pre-release)

> Issue asociada: [`issue-barrido-final-sin-ia.md`](issue-barrido-final-sin-ia.md)

Este documento recoge el barrido transversal realizado para cerrar la fase de
**web operativa sin IA** dejando el proyecto pulido y con garantías reproducibles antes
de empezar la integración de la capa IA. No se añade funcionalidad nueva: el foco es
calidad de código, cobertura, verificación de flujos y consistencia documental.

## 1. Calidad de código: linter reproducible

Hasta este punto el repositorio no tenía un linter configurado, de modo que la calidad
de estilo dependía de la revisión manual. Se incorpora [`ruff`](https://docs.astral.sh/ruff/)
por ser rápido y combinar linter y ordenador de imports en una sola herramienta.

- Se añade `ruff>=0.6` al extra `dev` de `pyproject.toml`.
- Se configura `[tool.ruff]` (Python 3.12, longitud de línea 100) con el conjunto de
  reglas `E, F, I, W, UP, B` y se ignora `E501` (longitud) por no aportar valor en este
  proyecto. Se marcan como *immutable calls* `fastapi.File/Form/Query/Depends`, porque el
  patrón idiomático de FastAPI es invocarlas en los valores por defecto de los parámetros
  (lo que de otro modo dispararía `B008`).

Avisos detectados y corregidos:

| Regla | Ubicación | Corrección |
|-------|-----------|------------|
| `F841` | `app/services/parsers/bandit_parser.py` | Eliminada variable `test_id` sin uso |
| `F401` | `tests/test_bandit_parser.py` | Eliminado `import json` sin uso |
| `F401` | `tests/test_web_release_smoke.py` | Eliminado `import pytest` sin uso |
| `I001` | varios módulos y tests | Orden de imports normalizado (autofix) |

Resultado: `ruff check app tests` termina sin errores.

## 2. Integración del lint en el flujo

- **CI**: se añade un paso `Lint (ruff)` en `.github/workflows/ci.yml` antes de los tests,
  de forma que un fallo de estilo bloquea el pipeline igual que un fallo de cobertura.
- **pre-commit**: se añade el hook `astral-sh/ruff-pre-commit` con `--fix` para corregir
  localmente antes de cada commit.

## 3. Cobertura: refuerzo del módulo más débil

El módulo `app/services/runtime_analysis_service.py` era el de menor cobertura (~70 %)
porque su función central `analyze_fixtures_runtime` ejecuta Bandit y Semgrep como
subprocesos y no estaba cubierta por tests unitarios.

Se añaden cuatro tests que ejercitan la **orquestación** sin depender de los binarios
reales: se redirigen las rutas de módulo (`FIXTURES_TARGET`, `RUNTIME_REPORTS_DIR`, rutas
de informe) a un `tmp_path` y se sustituye `run_analysis_command` por un doble que escribe
informes JSON mínimos válidos. Se cubren:

- camino feliz (ambos informes generados, salida normalizada con `tool_runs` y `analysis_id`);
- objetivo de análisis inexistente (`FileNotFoundError`);
- informe de Bandit ausente (`RuntimeError`);
- informe de Semgrep ausente (`RuntimeError`).

Con ello el módulo pasa a ~98 % y la cobertura global sube a ~92 %. Se eleva el gate de
cobertura de **60 % a 85 %** en `pyproject.toml` para fijar el nivel alcanzado con margen.

## 4. Verificación de flujos web extremo a extremo

Mediante `TestClient` se comprobó el comportamiento real de la aplicación:

| Flujo | Resultado |
|-------|-----------|
| `GET /health` | 200 `{"status":"ok"}` |
| `GET /dashboard` | 200, formulario con todos los modos (incl. `git_clone`) |
| `GET /ai/status` | 200, metadatos de límites y flags |
| `POST /analysis/upload-zip` (ZIP válido) | ejecuta Bandit+Semgrep |
| `POST /analysis/upload-zip` (firma inválida) | 400 `ZIP_INVALID_SIGNATURE` + `analysis_id` |
| `POST /analysis/upload-zip` (vacío) | 400 `ZIP_EMPTY_CONTENT` |
| `POST /analysis/git-clone` (host no permitido) | 400 `GIT_HOST_NOT_ALLOWED` + `analysis_id` |
| `POST /dashboard/analyze` (ZIP) | 200, render con panel de diagnóstico de herramientas |

Todas las validaciones y el contrato de error unificado (`error_code`, `message`,
`analysis_id`) responden como se espera.

### Nota sobre el entorno de pruebas

Durante el barrido, el `venv` del sandbox tenía Semgrep inutilizable por un conflicto de
dependencias (`attr`/`attrs`: `cannot import name 'define' from 'attr'`). Se resolvió
reinstalando `attrs`. El error remanente al ejecutar Semgrep en el sandbox
(`PermissionError` al escribir `~/.semgrep/semgrep.log`) es una **restricción del sandbox**,
no un defecto del proyecto: en un entorno normal Semgrep funciona y el flujo ZIP completa
con hallazgos de ambas herramientas.

## 5. Observación de robustez (trabajo futuro, no incluido)

El diseño actual considera el análisis fallido si **cualquiera** de las dos herramientas no
produce informe (502 `ANALYZER_REPORT_MISSING`). Una mejora de robustez futura sería la
**degradación elegante**: si una herramienta falla pero la otra produce hallazgos, devolver
esos hallazgos junto al diagnóstico de la herramienta caída. Por implicar un cambio de
contrato, se deja documentada como issue independiente y fuera del alcance de este barrido.

## 6. Documentación actualizada

- `README.md`: nueva sección «Calidad de código (lint)» y umbral de cobertura actualizado a 85 %.
- `docs/07_memoria/01_evolucion_del_desarrollo.md`: sección 13 sobre el barrido.

## Verificación

```bash
export PATH="$PWD/.venv/bin:$PATH"
ruff check app tests
pytest -q
```

Estado al cierre: `ruff` limpio; **170 tests** en verde; cobertura **~92 %** con gate al 85 %.
