# Avance: diagnóstico Bandit/Semgrep en dashboard

## Objetivo

Cuando un análisis runtime termina pero solo aparecen hallazgos de Bandit (o ninguno de Semgrep), el usuario debe poder ver que **las herramientas se ejecutaron** y con qué código de salida, sin abrir logs del servidor.

## Cambios implementados

### `app/services/presentable_scan.py`

- `build_tool_diagnostics(tool_runs, findings)`: resume por herramienta:
  - `returncode`
  - `status` / `status_label` (0 = ok, 1 = completado con hallazgos, ≥2 = error)
  - `findings_count` (conteo por `source_tool` en hallazgos normalizados)
  - `note` si terminó sin aportar filas
  - `stderr_preview` si existe en `tool_runs`
- `presentable_from_internal_analysis`: añade `meta.tool_diagnostics` cuando el payload interno incluye `tool_runs`.

### `app/templates/dashboard.html`

- Panel **«Diagnóstico Bandit / Semgrep»** entre resúmenes y listado de hallazgos.
- Tarjetas por herramienta con estado, returncode, conteo y stderr acotado.

Modos **informes estáticos** (sin `tool_runs`) no muestran el panel.

## Interpretación de returncode

| Código | Significado habitual (Bandit/Semgrep) |
|--------|----------------------------------------|
| 0 | Completado; la herramienta no reporta issues (o lista vacía) |
| 1 | Completado con hallazgos detectados |
| ≥2 | Error de ejecución o condición anómala |

## Pruebas

- `tests/test_presentable_scan.py` — `build_tool_diagnostics`, integración en presentable
- `tests/test_dashboard.py` — panel visible en fixture runtime

## Memoria

Nota en `docs/07_memoria/01_evolucion_del_desarrollo.md` (sección 12).
