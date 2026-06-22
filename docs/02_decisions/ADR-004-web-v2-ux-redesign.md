# ADR-004 — Rediseño web v2 (producto de defensa)

## Estado

Aceptada (fase 0–1 en curso). Sustituye la consola monolítica `/dashboard` como experiencia principal.

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

### Compatibilidad

- `GET /dashboard` → redirect **302** a `/analyze` (marcadores antiguos).
- `POST /dashboard/analyze` y `POST /dashboard/enrich-ai` se mantienen temporalmente para tests/CI; el flujo nuevo es el recomendado.
- Modos `fixture_*` permanecen en **API** y tests, no en la UI v2.

### Almacén de resultados

`ScanResultStore` guarda, además del payload interno:

- `analysis_mode`, `hide_info`, `group_equivalent`, `enable_ai_explanations`.

TTL en memoria ~60 min (sin disco). Tras reinicio del proceso o caducidad, `/results/{id}` muestra error claro.

### Fuera de alcance (fases posteriores)

- Rediseño visual completo (fase 2).
- Informe PDF/HTML imprimible (fase 5).
- Despliegue VPS documentado (fase 6).

## Consecuencias

- Tests de humo actualizados hacia rutas v2.
- `manual-usuario-web.md` quedará desactualizado hasta fase 2 (se actualizará con capturas nuevas).
- La demo de defensa usará `vulnerable_demo.zip` subido por el formulario `/analyze`.

## Referencias

- [WEB v2 issue fase 0–1](../04_delivery/issue-web-v2-fase-0-1-rutas.md)
- [ADR-003](ADR-003-ai-explanations-design.md) — capa IA
- [WEB-5](../04_delivery/issue-web-5-enriquecer-ia-sin-reescanear.md) — enrich sin re-escanear
