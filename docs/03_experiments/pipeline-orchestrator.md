# Orquestador del pipeline (MVP)

## Qué problema resuelve

Hasta ahora el flujo estaba repartido: parsers, loader, mapper y verificadores por caso. Para la memoria y para la API hacía falta una capa que unifique la vista del pipeline después de clasificar los hallazgos y, aparte, poder lanzar la ronda de verificación autofix sobre los fixtures del MVP.

## Qué hace el módulo `pipeline_orchestrator`

1. **`build_pipeline_view(findings)`**
   A partir de la lista ya enriquecida (`NormalizedFinding`), devuelve conteos por `mvp_category` y por `remediation_mode`, y agrupa los hallazgos por categoría. Es el paso detect → classify en forma de respuesta estable.

2. **`run_mvp_autofix_verification_roundtrip()`**
   Para cada categoría del MVP con autofix, lee los ficheros canónicos del corpus y ejecuta el verificador correspondiente (que internamente hace remediación + Bandit + Semgrep). **No incluye SQL injection**, que en el proyecto sigue como `proposal_only`.

## Integración en la API

- `GET /analysis/fixtures` y `POST /analysis/run-fixtures` incluyen un campo **`pipeline`** con la salida de `build_pipeline_view`.
- `GET /analysis/pipeline/mvp-autofix-verification` devuelve solo la ronda de verificación autofix. Puede tardar bastante porque lanza herramientas varias veces; está pensado para pruebas y demos, no para llamarlo en bucle en producción.

## Limitaciones

- La agrupación duplica información respecto a la lista plana `findings`; es a cambio de tener una vista por categoría sin otro endpoint intermedio.
- La ronda MVP usa rutas fijas a los fixtures del repositorio; si cambia el corpus, hay que actualizar el mapa en código.
