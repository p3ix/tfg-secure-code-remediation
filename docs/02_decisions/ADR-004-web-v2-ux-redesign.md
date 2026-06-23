# ADR-004 — Rediseño web v2 (producto de defensa)

## Estado

Aceptada (fases 0–5). Sustituye la consola monolítica `/dashboard` como experiencia principal.

## Contexto

La consola web actual mezcla formulario, modos MVP/demo y resultados en una sola página (`/dashboard`).
Para la defensa del TFG y el despliegue en VPS con dominio propio se necesita:

- Pantalla de **inicio** orientada al usuario final.
- Flujo **analizar → página de resultados** (PRG: POST-Redirect-GET).
- Solo modos **reales** en la UI pública (ZIP, Git HTTPS, ruta local).
- Elección explícita **con/sin IA**; enriquecimiento posterior (WEB-5) en resultados.
- ZIP de demostración: `vulnerable_demo.zip` en la raíz del repositorio.

El núcleo backend (SAST, presentable, IA, almacén efímero) se reutiliza.

## Decisión

### Rutas web v2 (fase 1)

| Ruta | Método | Rol |
|------|--------|-----|
| `/` | GET | Landing: qué hace la app, enlace a analizar |
| `/analyze` | GET | Formulario de análisis (solo modos reales) |
| `/analyze` | POST | Ejecuta SAST; guarda en `ScanResultStore`; redirect 303 → `/results/{analysis_id}` |
| `/results/{analysis_id}` | GET | Resultados presentables; filtros vía query |
| `/results/{analysis_id}/enrich-ai` | POST | Añade IA sin re-escanear; redirect al mismo resultado |
| `/results/{analysis_id}/report` | GET | Informe HTML imprimible |
| `/results/{analysis_id}/export.json` | GET | Exportación JSON del presentable |

### Compatibilidad

- `GET /dashboard` → redirect **302** a `/analyze` (marcadores antiguos).
- `POST /dashboard/analyze` y `POST /dashboard/enrich-ai` se mantienen temporalmente para tests/CI; el flujo nuevo es el recomendado.
- Modos `fixture_*` permanecen en **API** y tests, no en la UI v2.

### Almacén de resultados

`ScanResultStore` guarda, además del payload interno:

- `analysis_mode`, `hide_info`, `group_equivalent`, `enable_ai_explanations`.

TTL en memoria ~60 min (sin disco). Tras reinicio del proceso o caducidad, `/results/{id}` muestra error claro.

### Fase 3 (cerrada)

- Sección «Explicaciones IA» explícita en `/analyze` (toggle o aviso si capa desactivada).
- Filtros de vista en `/results/{id}` vía `POST /results/{id}/view-prefs` sin re-SAST.
- Banner de estado IA y mensajes según proveedor (stub/Ollama).
- Enrich WEB-5 integrado con preferencias de vista persistidas.

### Fase 4 (cerrada)

- Layout split-scroll: sidebar (metadatos, filtros, índice) + panel principal de hallazgos.
- Cabecera con objetivo y conteo; anclas `#finding-{id}` e índice navegable.
- Filtros compartibles por query (`?hide_info=true&group_equivalent=true`).
- Diagnóstico de herramientas colapsable; barra móvil «Nuevo análisis».

### Fase 5 (cerrada)

- `GET /results/{analysis_id}/report` — HTML imprimible (`report.html`, `report.css`).
- `GET /results/{analysis_id}/export.json` — presentable JSON con filtros vía query.
- Enlaces «Informe imprimible» y «Exportar JSON» en resultados.

### Fuera de alcance (fases posteriores)

- Despliegue VPS documentado (fase 6).

### Fase 2 (cerrada)

- Tipografía sans para lectura y mono para código/metadatos.
- Landing con flujo «Cómo funciona» en tres pasos.
- Formulario `/analyze` con secciones numeradas y campos visibles según modo.
- Resultados con breadcrumb, toolbar y estados de error accesibles.
- Manual de usuario actualizado (`manual-usuario-web.md`).

## Consecuencias

- Tests de humo actualizados hacia rutas v2.
- `manual-usuario-web.md` actualizado en fase 2 (rutas v2).
- La demo de defensa usará `vulnerable_demo.zip` subido por el formulario `/analyze`.

## Referencias

- [WEB v2 issue fase 0–1](../04_delivery/issue-web-v2-fase-0-1-rutas.md)
- [WEB v2 issue fase 2](../04_delivery/issue-web-v2-fase-2-visual.md)
- [WEB v2 issue fase 3](../04_delivery/issue-web-v2-fase-3-ai-experience.md)
- [WEB v2 issue fase 4](../04_delivery/issue-web-v2-fase-4-results-complete.md)
- [WEB v2 issue fase 5](../04_delivery/issue-web-v2-fase-5-informe-exportable.md)
- [ADR-003](ADR-003-ai-explanations-design.md) — capa IA
- [WEB-5](../04_delivery/issue-web-5-enriquecer-ia-sin-reescanear.md) — enrich sin re-escanear
