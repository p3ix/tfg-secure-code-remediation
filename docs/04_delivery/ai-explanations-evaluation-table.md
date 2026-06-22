# Evaluación cualitativa de las explicaciones IA

Este documento define cómo se evalúa la utilidad de la capa de explicaciones asistidas por
IA del proyecto (ADR-003) y recoge los resultados sobre el corpus `fixtures/mvp/`. La capa
es **opcional y degradable**: el núcleo detect→classify→verify no depende de ella. Aquí se
mide la calidad del texto generado, no la detección (que la aportan Bandit/Semgrep).

## Metodología

- **Entrada**: cada hallazgo normalizado del corpus MVP (categoría, regla, CWE/OWASP,
  severidad, mensaje, fichero/línea). El `code_focus` se deriva del parser (`code_snippet`
  o mensaje); el modelo no es la única fuente de contexto. El snippet completo solo se envía
  a Ollama si `TFG_AI_INCLUDE_SNIPPET=1`.
- **Proveedores comparados**:
  - `stub` — línea base determinista, sin red (tests/CI y demo offline).
  - `ollama` — modelo local recomendado (p. ej. `llama3.2:3b`), reproducible en la máquina.
- **Trazabilidad**: cada explicación registra `provider`, `model`, `prompt_version` (**v3**)
  y `prompt_hash`, de modo que un resultado puntuado puede reproducirse con la misma versión
  de prompt.
- **Revisión**: humana (autor del TFG), una pasada por categoría.

## Rúbrica (0–2 por criterio; máximo 6 por explicación)

| Criterio | 0 | 1 | 2 |
|----------|---|---|---|
| **Correctitud técnica** | Incorrecta o engañosa | Parcialmente correcta | Correcta y precisa |
| **Utilidad pedagógica** | No ayuda a entender | Ayuda de forma genérica | Explica el porqué y orienta la solución |
| **Ausencia de alucinación** | Inventa hechos/APIs | Alguna imprecisión menor | Sin afirmaciones inventadas |

Interpretación: 5–6 = útil para memoria/demo; 3–4 = aceptable con revisión; 0–2 = descartar.

## Cómo reproducir

```bash
export PATH="$PWD/.venv/bin:$PATH"
# Línea base determinista (offline):
TFG_AI_EXPLANATIONS_ENABLED=1 TFG_AI_PROVIDER=stub \
  uvicorn app.main:app --reload    # ver /dashboard o /analysis/fixtures/presentable

# Modelo local (requiere Ollama y el modelo descargado):
ollama pull llama3.2:3b
TFG_AI_EXPLANATIONS_ENABLED=1 TFG_AI_PROVIDER=ollama TFG_AI_MODEL=llama3.2:3b \
  uvicorn app.main:app --reload
```

## Resultados — línea base `stub` (determinista, prompt v3)

Tras **IA-8**, el stub incluye `location_hint`, `code_focus` (desde el hallazgo) y
`action_steps` por categoría MVP. Sigue siendo determinista y sin alucinación; la pedagogía
mejora respecto a v2 al anclar la explicación a fichero/línea y pasos concretos.

| Categoría MVP | Resumen (stub) | Correctitud | Pedagogía | No alucinación | Total |
|---------------|----------------|:-----------:|:---------:|:--------------:|:-----:|
| command_injection | Ejecución de comandos con entrada no confiable | 2 | 2 | 2 | 6 |
| yaml_load | Deserialización insegura de YAML | 2 | 2 | 2 | 6 |
| flask_debug | Flask con modo debug activado | 2 | 2 | 2 | 6 |
| requests_timeout | Petición HTTP sin timeout | 2 | 2 | 2 | 6 |
| verify_false | Verificación TLS desactivada | 2 | 2 | 2 | 6 |

## Resultados — `ollama` (modelo local, prompt v3)

> Pendiente de rellenar ejecutando el modelo local en la máquina de desarrollo
> (el sandbox de CI no tiene Ollama). Se puntúa con la rúbrica anterior; se anota
> `model` y `prompt_version` usados para trazabilidad. Se espera pedagogía ≥ stub v3
> al contextualizar con fichero/línea y pasos generados.

| Categoría MVP | Modelo | Correctitud | Pedagogía | No alucinación | Total | Observaciones |
|---------------|--------|:-----------:|:---------:|:--------------:|:-----:|---------------|
| command_injection | _por completar_ | | | | | |
| yaml_load | _por completar_ | | | | | |
| flask_debug | _por completar_ | | | | | |
| requests_timeout | _por completar_ | | | | | |
| verify_false | _por completar_ | | | | | |

## Conclusión (provisional)

- El **stub v3** (IA-8) garantiza explicación correcta, ubicación explícita y pasos de
  remediación reproducibles offline; puntuación pedagógica 2 en todas las categorías MVP.
- El modelo local `ollama` con **prompt v3** debe aportar utilidad pedagógica adicional
  sobre casos concretos. La comparación stub vs ollama es el material de evaluación del TFG.
- En todos los casos la IA es **complemento**: la verificación de que el problema existe y
  de que la remediación funciona la siguen aportando Bandit/Semgrep y los remediadores
  deterministas.

> Relacionado: [tabla de evaluación del MVP](mvp-evaluation-table.md), [ADR-003](../02_decisions/ADR-003-ai-explanations-design.md).
