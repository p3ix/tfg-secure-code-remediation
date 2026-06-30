# Release: web operativa con IA (v0.2.0)

## Resumen

Sobre el núcleo de análisis ya operativo (v0.1.0), esta release integra la **capa IA de
explicación asistida** sobre los hallazgos normalizados (ADR-003). Desde el navegador se puede
analizar código Python real **y**, opcionalmente, obtener explicaciones generadas por un modelo
(Ollama local recomendado), incluyendo un **ejemplo antes/después**.

La capa IA es **opcional y degradable**: el núcleo detect→classify→verify (Bandit + Semgrep) no
depende de ella. Por defecto permanece desactivada (`TFG_AI_EXPLANATIONS_ENABLED=false`) para
garantizar un arranque limpio, reproducible y sin dependencias de red; activarla requiere un
proveedor configurado y mantiene la supervisión humana.

## Qué incluye este hito

### Capa IA de explicación (ADR-003)

| Elemento | Estado |
|----------|--------|
| Contrato `AIExplanation` (schema 1.2) con ejemplo antes/después | Operativo |
| Proveedor `stub` (determinista, offline, tests/demo) | Operativo |
| Proveedor `ollama` (modelo local, p. ej. `llama3.2:3b`) | Operativo (requiere Ollama) |
| Proveedor `openai` (API opcional) | Operativo (requiere `OPENAI_API_KEY`) |
| Prompt v4 con trazabilidad (`provider`, `model`, `prompt_version`, `prompt_hash`) | Operativo |
| Render visual del ejemplo antes/después en web e informe | Operativo |
| Caché de explicaciones por `analysis_id` en `ScanResultStore` | Operativo |

### Plataforma (heredado de v0.1.0, sigue operativo)

| Modo | Tipo | Estado |
|------|------|--------|
| Subir ZIP | Real | Operativo |
| Clonar repositorio Git (HTTPS) | Real | Operativo (sujeto a `TFG_ENABLE_GIT_CLONE` y hosts permitidos) |
| Ruta local permitida | Real | Operativo (requiere `TFG_LOCAL_ANALYSIS_ROOT` y `TFG_ENABLE_LOCAL_PATH`) |
| Informes guardados / runtime (fixtures) | MVP/demo | Operativo |

### Operación y seguridad

- IA **desactivada por defecto** (`TFG_AI_EXPLANATIONS_ENABLED=false`) y snippet de código al
  modelo **opt-in** (`TFG_AI_INCLUDE_SNIPPET=false`) por privacidad.
- **Persistencia de resultados en disco** (`TFG_SCAN_STORE_DIR`): sobreviven a reinicios, con
  purga por TTL (`TFG_SCAN_STORE_TTL_SEC`) y número máximo (`TFG_SCAN_STORE_MAX_ENTRIES`).
- Límites de IA: `TFG_AI_TIMEOUT_SEC`, selección de `TFG_AI_PROVIDER` / `TFG_AI_MODEL`.

### Evaluación

- Harness de evaluación cuantitativa del MVP (`app/services/evaluation/`).
- Rúbrica y resultados cualitativos de las explicaciones: ver
  [ai-explanations-evaluation-table.md](ai-explanations-evaluation-table.md).

## Fuera de alcance de este hito

- Autofix completo sobre proyectos reales arbitrarios (solo patrones MVP acotados en el pipeline
  de verificación determinista).
- IA activada por defecto o como requisito del flujo (sigue siendo complemento supervisado).
- Autenticación multiusuario y endurecimiento de producción (TLS, rate limiting global, etc.).

## Verificación manual recomendada

1. Arrancar la API sin IA: `uvicorn app.main:app --reload` y confirmar análisis operativo.
2. Consultar `GET /ai/status` y confirmar `ai_explanations_enabled: false` en entorno por defecto.
3. Activar la línea base determinista (offline):
   `TFG_AI_EXPLANATIONS_ENABLED=1 TFG_AI_PROVIDER=stub uvicorn app.main:app --reload` y revisar
   que cada hallazgo muestra explicación y ejemplo antes/después.
4. Con Ollama disponible: `ollama pull llama3.2:3b` y
   `TFG_AI_EXPLANATIONS_ENABLED=1 TFG_AI_PROVIDER=ollama TFG_AI_MODEL=llama3.2:3b uvicorn app.main:app --reload`.
5. Comprobar que `/results/{id}` y `/results/{id}/report` no re-invocan el modelo en cada carga
   (caché por `analysis_id`).

## Verificación automatizada

```bash
.venv/bin/ruff check .
.venv/bin/pytest -q tests/test_web_release_smoke.py tests/test_dashboard.py
.venv/bin/pytest -q
```

La suite (281 tests, gate de cobertura 85%) cubre el flujo IA en web (enriquecimiento sin
re-SAST), el parser tolerante de Ollama y el presentable con IA, y verifica que la IA **no** es
requisito del estado por defecto.

## Siguiente fase

Ampliar el autofix asistido más allá de los patrones MVP y completar la tabla de evaluación
`ollama` con el modelo local en la máquina de desarrollo.

---

*Hito cerrado como entrega del TFG — fase «análisis real vía web con capa IA de explicación».*
