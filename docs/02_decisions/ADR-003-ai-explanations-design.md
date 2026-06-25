# ADR-003 — Diseño de la capa de IA (explicación asistida de hallazgos)

## Estado

Aceptada (diseño de la fase IA). Complementa al [ADR-002](ADR-002-ai-assisted-roadmap.md), que fijó el *roadmap*; este ADR fija el **diseño** concreto antes de implementar.

## Contexto

El MVP cierra la fase «web operativa sin IA» (release `v0.1.0`): detección SAST (Bandit + Semgrep), modelo normalizado, clasificación CWE/OWASP/ASVS, remediación determinista acotada con verificación por re-análisis, y consola web. El título del TFG menciona remediación **asistida por IA**; toca incorporar esa capa **sin** comprometer la verificabilidad ni la reproducibilidad del núcleo.

El proyecto analiza **código de terceros** (ZIP subido, repos clonados, rutas locales). Enviar fragmentos de ese código a servicios externos es un riesgo de privacidad poco coherente con un trabajo de seguridad. Además, la memoria y la defensa del TFG necesitan **reproducibilidad** y una demo que funcione **sin red ni claves**.

El ADR-002 ya estableció los principios: IA **opcional**, desactivada por defecto (`TFG_AI_EXPLANATIONS_ENABLED`), con supervisión humana y trazabilidad alineadas con NIST SP 800-218A ([REF-017](../06_references/README.md)). Este ADR concreta rol, arquitectura, datos, seguridad, salida y evaluación.

## Decisión

### 1. Rol de la IA — explicación, sugerencia y ejemplo ilustrativo; nunca un parche aplicado ni verificado

La IA produce, por hallazgo:

- una **explicación** (riesgo, impacto y por qué es un problema, citando CWE/OWASP);
- una **sugerencia de remediación en lenguaje natural** (cómo se corregiría, a alto nivel); y
- un **ejemplo ilustrativo "antes / después"** del patrón (fragmento *vulnerable → corregido*), con fines pedagógicos.

> **Revisión (post-release v0.1.0):** la versión original de este ADR prohibía que la IA *generara código*. Esa regla se **flexibiliza**: se permite el ejemplo ilustrativo "antes/después" porque mejora notablemente la claridad y el **coste/riesgo es bajo en este diseño** — el modelo es **local (Ollama)**, así que el ejemplo se genera en la máquina sin enviar nada fuera, y es **material educativo mostrado en la UI**, no un parche que se aplique al proyecto del usuario.

La IA **no aplica cambios sobre el código del usuario, no descarga parches y no emite garantía de corrección**: el ejemplo "antes/después" **no se verifica por reescaneo**. Las remediaciones **aplicadas y verificadas** siguen siendo exclusivamente las de los *remediators* deterministas, validadas por el módulo de verificación (re-ejecución SAST). El flujo detect→repair→verify no depende de la IA.

**Distinción que se mantiene como invariante:** *ejemplo ilustrativo de IA* (orientativo, en cualquier hallazgo) ≠ *parche determinista verificado* (aplicado y comprobado por reescaneo, solo en categorías acotadas). La IA aporta cobertura educativa; los remediators, garantía.

### 2. Arquitectura — `AIProvider` con tres implementaciones (local primero)

Se introduce una abstracción `AIProvider` con un método del estilo `explain(finding) -> AIExplanation`, seleccionada por `TFG_AI_PROVIDER`:

| Proveedor | Uso | Red | Clave |
|-----------|-----|-----|-------|
| `StubProvider` | Tests, CI y demo offline | No | No |
| `OllamaProvider` | Uso real (**default recomendado**) | No (localhost) | No |
| `OpenAIProvider` | Comparativa de calidad (opt-in) | Sí | Sí |

- **`StubProvider`:** determinista, sin red. **Default en tests/CI.** Permite cablear el contrato extremo a extremo (modelo → presentable → dashboard) y mantener la suite offline y reproducible.
- **`OllamaProvider`:** modelo local vía [Ollama](https://ollama.com/) ([REF-021](../06_references/README.md)). **Default recomendado** en uso real del TFG. Modelos pequeños cuantizados acordes al hardware (p. ej. `llama3.2:3b` o `qwen2.5:7b` en Q4): privacidad (el código no sale de la máquina), coste cero y disponibilidad offline en la defensa.
- **`OpenAIProvider`** (u otra API, p. ej. [REF-019](../06_references/README.md)): **opcional, opt-in**, solo para comparativa de calidad en la evaluación. Requiere clave en `.env` (nunca versionada).

Orden de implementación previsto: (1) `StubProvider` + contrato de salida; (2) `OllamaProvider` + caché; (3) API externa solo si aporta material a la evaluación.

### 3. Activación y seguridad — opcional y degradable

- `TFG_AI_EXPLANATIONS_ENABLED=0` por defecto (ya existe en `config.py`).
- Configuración prevista: `TFG_AI_PROVIDER`, `TFG_AI_MODEL`, `TFG_AI_OLLAMA_URL`, `TFG_AI_TIMEOUT_SEC`, `TFG_AI_MAX_OUTPUT_TOKENS`, `TFG_AI_INCLUDE_SNIPPET`. Clave de API solo en `.env` (ya en `.gitignore`), **nunca** en el repositorio.
- **Degradación limpia**: si la IA está desactivada, falla o supera el *timeout*, `ai_explanation` queda `null` y el análisis responde con normalidad. La IA nunca puede tumbar un escaneo.

### 4. Qué se envía al modelo — hallazgo normalizado; snippet opt-in

Por defecto se envía solo el **hallazgo normalizado** (regla, CWE/OWASP, severidad, mensaje, categoría MVP). El envío del `code_snippet` es **opt-in** mediante `TFG_AI_INCLUDE_SNIPPET=0` (desactivado por defecto) por motivos de privacidad. **No** se envía el fichero completo ni el árbol del proyecto.

Si se activa un provider externo (`openai`), los fragmentos enviados salen hacia la API; se documenta explícitamente como riesgo (coherente con NIST SP 800-218A). Con Ollama en localhost el código permanece en la máquina.

### 5. Caché y determinismo

Las explicaciones se cachean por clave `(provider, model, mvp_category, cwe_id, source_rule_id[, hash_snippet])` — no por fichero/línea — para reducir llamadas, abaratar y dar reproducibilidad citable en la memoria. Implementación inicial en memoria; persistencia en disco como mejora opcional.

Para **enriquecer con IA sin re-escanear** (WEB-5), el dashboard guarda el payload interno del último análisis web exitoso en un almacén efímero en memoria, indexado por `analysis_id` y con TTL de ~60 minutos. Permite regenerar solo la capa explicativa; no sustituye la persistencia de informes SAST.

### 6. Contrato de salida — `ai_explanation` opcional, `schema_version` 1.1

Se añade `ai_explanation: AIExplanation | None` al JSON presentable por hallazgo (y por grupo equivalente) y un bloque correspondiente en el dashboard. El campo es **opcional** y se sube `schema_version` a **1.1** para no romper a los consumidores ni los tests del 1.0. La respuesta registra `model` y `prompt_version` cuando hay generación (trazabilidad).

### 7. Evaluación — revisión cualitativa sobre el corpus

La utilidad de la IA se evalúa con una **tabla de evaluación** (estilo `docs/04_delivery/mvp-evaluation-table.md`) puntuando cada explicación en correctitud técnica, utilidad pedagógica y ausencia de alucinación, sobre el corpus `fixtures/mvp/` y algún proyecto real. Revisión humana; se documenta modelo y prompt usados. Opcionalmente se compara calidad **local (Ollama) vs API**.

### Decisiones transversales

- **Trazabilidad del prompt**: registrar `model`, `prompt_version` y un hash del prompt en la respuesta (requisito NIST SP 800-218A, no extra).
- **Idioma**: explicaciones en castellano (coherente con la memoria), configurable.
- **Prompt injection**: `raw_message`/`code_snippet` se inyectan en un bloque delimitado y el *system prompt* instruye a tratarlos como **dato no confiable** (se analiza código de terceros). Ver [REF-020](../06_references/README.md).
- **Disclaimer en UI**: la explicación es generada por IA y puede contener errores; la verificación la aportan Bandit/Semgrep. Refuerza la supervisión humana.

## Opciones consideradas

| Opción | Ventajas | Inconvenientes | Decisión |
|--------|----------|----------------|----------|
| Solo API externa (OpenAI/Anthropic) | Mejor calidad, cero hardware | Envía código de terceros a un tercero; depende de red/clave/cuota | Descartada como principal |
| Solo IA local (Ollama) | Privada, gratis, offline | Menor calidad; dependiente del hardware | Adoptada como principal |
| Híbrida con abstracción | Local por defecto, stub para tests, API opcional para comparar | Complejidad extra de la abstracción | **Elegida** |

## Consecuencias

- El núcleo detect→classify→verify y sus tests siguen sin depender de IA; la suite y el CI permanecen offline gracias al `StubProvider`.
- Privacidad por diseño con la configuración por defecto (`ollama` en localhost, snippet desactivado).
- Demo y defensa del TFG sin depender de red ni clave externa.
- La memoria puede describir evaluación comparable (local vs API) sobre un punto de extensión ya definido.
- El contrato `schema_version` 1.1 con campo opcional evita una rotura incompatible al conectar proveedores reales.

**Negativas / asumidas:** calidad y latencia del modelo local por debajo de modelos cloud grandes; requisitos de hardware para Ollama; complejidad de la abstracción y la caché (compensada con testabilidad).

## Variables de entorno (resumen)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `TFG_AI_EXPLANATIONS_ENABLED` | `0` | Activa/desactiva la capa IA |
| `TFG_AI_PROVIDER` | `ollama` | `stub`, `ollama` o `openai` |
| `TFG_AI_MODEL` | `llama3.2:3b` | Modelo (Ollama o API) |
| `TFG_AI_OLLAMA_URL` | `http://127.0.0.1:11434` | Endpoint de Ollama |
| `TFG_AI_TIMEOUT_SEC` | `30` | Timeout por llamada (segundos) |
| `TFG_AI_MAX_OUTPUT_TOKENS` | (p. ej. `512`) | Tope de salida / coste |
| `TFG_AI_INCLUDE_SNIPPET` | `0` | Incluir snippet de código en el prompt |
| `OPENAI_API_KEY` | (vacío) | Solo si `TFG_AI_PROVIDER=openai` |

## Seguimiento (próximas issues)

1. Definir interfaz `AIProvider` + `StubProvider` (con tests) sin tocar el núcleo.
2. Integrar `OllamaProvider` y la caché de explicaciones.
3. Añadir `ai_explanation` al presentable, subir `schema_version` a 1.1 y render en dashboard.
4. Diseñar la evaluación cualitativa sobre el corpus MVP (opcional comparativa API).

## Referencias

- [ADR-002](ADR-002-ai-assisted-roadmap.md) — *roadmap* y principios de la IA asistida.
- [REF-017](../06_references/README.md) — NIST SP 800-218A (prácticas con modelos generativos y doble uso; supervisión humana y trazabilidad).
- [REF-019](../06_references/README.md) — Anthropic Claude API / SDK (proveedor API opcional para comparativa).
- [REF-020](../06_references/README.md) — OWASP Top 10 for LLM Applications (prompt injection y riesgos de aplicaciones con LLM).
- [REF-021](../06_references/README.md) — Ollama (proveedor local recomendado).
- [`docs/00_scope.md`](../00_scope.md) — alcance y supervisión humana.
