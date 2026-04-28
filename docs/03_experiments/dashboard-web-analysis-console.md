# Dashboard web de análisis

## Objetivo

Evolucionar `/dashboard` desde una vista pasiva de resultados a una **consola web mínima de producto**, capaz de lanzar análisis desde navegador y renderizar el resultado con la misma capa presentable usada por la API.

## Motivación

Hasta este punto del repositorio, la interfaz HTML mostraba bien el escaneo del corpus MVP, pero quedaba más cerca de una tabla técnica que de una aplicación web defendible ante tribunal. La necesidad era doble:

- **visibilidad de producto**: que el flujo principal pudiera demostrarse sin salir del navegador;
- **coherencia arquitectónica**: reutilizar servicios ya existentes (`analyze_fixtures_reports`, `analyze_fixtures_runtime`, `analyze_zip_bytes`, `analyze_local_path_relative`) sin duplicar lógica de análisis en la capa web.

## Alcance de esta iteración

La iteración incorpora:

1. **Formulario web unificado** en `/dashboard` para:
   - cargar informes estáticos del corpus MVP;
   - ejecutar análisis runtime sobre `fixtures/mvp`;
   - subir un ZIP con código Python;
   - analizar una ruta local relativa si `TFG_LOCAL_ANALYSIS_ROOT` está configurado.
2. **Render del resultado en la misma plantilla**, sin redirigir al usuario a JSON crudo.
3. **Filtros de presentación** (`hide_info`, `group_equivalent`) desde la propia interfaz.
4. **Mensajes de error visibles** en HTML cuando falla el análisis.

## Decisiones de diseño

- Se mantiene la **API existente**; la interfaz web es una capa adicional, no un reemplazo de endpoints.
- El render usa el mismo flujo `presentable_from_internal_analysis` + `filter_presentable_scan`, de modo que la vista HTML y la salida JSON compartan semántica.
- La interacción se resuelve con **HTML del lado servidor** (FastAPI + Jinja), sin introducir JavaScript como dependencia del MVP.
- El modo por defecto sigue siendo cargar los **informes estáticos** del corpus, útil para demos rápidas y para entornos donde Bandit/Semgrep no estén disponibles en tiempo real.

## Resultado esperado en demo

Con esta mejora, el TFG se puede enseñar como una **aplicación web funcional**:

- se abre `/dashboard`;
- se elige el tipo de análisis;
- se ejecuta desde la propia interfaz;
- se muestran tarjetas resumen, categorías y hallazgos con mejor jerarquía visual.

Esto mejora la defensa oral porque el proyecto deja de depender de explicar endpoints o enseñar JSON como interfaz principal.

## Archivos principales

- `app/main.py`
- `app/templates/dashboard.html`
- `tests/test_dashboard.py`
- `README.md`

## Límites

- No hay persistencia de análisis entre peticiones.
- No se ha incorporado aún una vista web para clonado Git, por mantener esta iteración centrada en ZIP, fixtures y ruta local.
- La capa IA para remediación sigue fuera de esta iteración; la consola web prepara mejor ese encaje futuro, pero no depende de él.
