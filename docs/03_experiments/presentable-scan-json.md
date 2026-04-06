# JSON de salida presentable (vista escaneo)

## Objetivo

Tener un contrato de respuesta estable para ver el resultado de un escaneo como lo vería un usuario o la memoria del TFG, sin el volcado interno (`raw_tool_data`) ni ruido de depuración.

## Versión del esquema

El campo `schema_version` (actualmente `1.0`) permite evolucionar el formato sin romper clientes si más adelante se añaden campos.

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/analysis/fixtures/presentable` | Reports Bandit/Semgrep ya generados en `reports/` |
| POST | `/analysis/run-fixtures/presentable` | Ejecuta Bandit y Semgrep sobre `fixtures/mvp` y devuelve la misma forma |

Query opcional en ambos: **`hide_info=true`** — recorta hallazgos con `remediation_mode` solo detección o severidad baja; útil para demos. Ver [docs/04_delivery/scan-noise-and-duplicates.md](../04_delivery/scan-noise-and-duplicates.md).

Las respuestas internas (`/analysis/fixtures` y `/analysis/run-fixtures`) siguen existiendo para depuración.

## Estructura resumida

- `meta`: objetivo del análisis, modo de ejecución, fecha ISO, nota breve, rutas a informes si aplica, y si se usó filtro demo (`presentable_filter`, `presentable_filter_note`).
- `summary`: totales y conteos por severidad, categoría MVP y modo de remediación.
- `findings`: lista de hallazgos con `id` secuencial, título, severidad (y etiqueta en castellano), fichero, líneas, herramienta, regla, mensaje acotado, estándares (CWE/OWASP) y bloque `remediation` con etiqueta legible del modo.

## Limitaciones

- Los mensajes se truncan a 2000 caracteres.
- No se incluye el JSON crudo de Bandit/Semgrep por hallazgo.
