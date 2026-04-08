# Agrupación de hallazgos equivalentes (Bandit + Semgrep)

## Objetivo

Documentar la implementación del parámetro **`group_equivalent`** en la vista presentable: agrupa hallazgos que comparten **mismo fichero** (ruta normalizada), **misma línea** y **misma categoría MVP**, sin perder la lista de herramientas y reglas que dispararon el aviso.

## Criterio de equivalencia

Definido en [`app/services/findings_dedup.py`](../../app/services/findings_dedup.py):

- `Path(file_path).as_posix()` + `line_start` + `mvp_category`

## Comportamiento

- **Modo plano** (`group_equivalent=false`, por defecto): una fila por hallazgo normalizado; mismo comportamiento que antes del cambio.
- **Modo agrupado** (`group_equivalent=true`): una fila por grupo; severidad = máxima del grupo; campos `sources` (lista de `tool`, `rule_id`, `rule_name`) y `group_size`; `meta.group_equivalent` y nota explicativa.

Los endpoints `GET /analysis/fixtures/presentable`, `POST /analysis/run-fixtures/presentable` y `GET /dashboard` aceptan el query parameter `group_equivalent=true`.

## Relación con ruido y duplicados

Ver [`docs/04_delivery/scan-noise-and-duplicates.md`](../04_delivery/scan-noise-and-duplicates.md): el parámetro `hide_info` reduce avisos informativos; la agrupación reduce filas duplicadas por solapamiento entre herramientas.
