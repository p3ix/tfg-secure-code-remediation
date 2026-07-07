# Changelog

Todos los cambios relevantes de este proyecto se documentan en este fichero.

El formato sigue, de forma aproximada, [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

- Líneas futuras recogidas en la memoria del TFG: evaluación sobre repositorios reales, remediación sobre código del usuario, integración en CI/CD y exportador SARIF.

## [1.0.0] - 2026-07-07

Versión final entregada como Trabajo Fin de Grado.

### Añadido
- **Vídeos de demostración** en `videos/` (instalación y despliegue, instalación de Ollama, configuración y análisis por ruta local, análisis por clonado Git y demo de remediación determinista), documentados en [`videos/README.md`](videos/README.md).
- Script `scripts/demo_remediacion.py`: ciclo completo detecta→corrige→reverifica sobre los fixtures de autofix del MVP (6/6 corregidos y verificados).

### Arreglado
- Resolución del binario de **Semgrep** junto al intérprete del entorno virtual, evitando el fallback deprecado `python -m semgrep`.

### Cambiado
- **README** reescrito: estado real del proyecto, rutas de la consola web v2 y capa de IA.
- `/ai/status` refleja que la capa de IA está implementada (desactivada por defecto).
- La CLI de evaluación escribe sus reportes en `var/evaluation/`.
- Limpieza de referencias internas a documentación no distribuida con el repositorio.

## [0.2.0] - 2026-06-30

Segunda release: **web de análisis de seguridad operativa con capa IA de explicación**.

La capa IA es **opcional y degradable**: el núcleo detect→classify→verify (Bandit + Semgrep) no depende de ella y la web sigue operativa con `TFG_AI_EXPLANATIONS_ENABLED=false` (valor por defecto). Activarla requiere un proveedor (Ollama local recomendado) y supervisión humana.

### Añadido
- **Explicaciones asistidas por IA** sobre hallazgos normalizados (ADR-003): contrato `AIExplanation` con **schema 1.2** (resumen, riesgo, ubicación, pasos de acción y **ejemplo antes/después**).
- **Proveedores de IA** seleccionables (`TFG_AI_PROVIDER`): `stub` (línea base determinista offline para tests/demo), `ollama` (modelo local, p. ej. `llama3.2:3b`) y `openai` (API opcional).
- **Prompt v4** tolerante con ejemplo antes/después, trazabilidad por `provider`, `model`, `prompt_version` y `prompt_hash`.
- **Render visual** del ejemplo antes/después de la IA en la web (resultados e informe).
- **Caché de explicaciones por `analysis_id`** en `ScanResultStore` (evita re-invocar el modelo en cada render de `/results` y `/report`).
- **Persistencia de resultados en disco** (`TFG_SCAN_STORE_DIR`): los análisis sobreviven a reinicios, con purga por TTL y número máximo de entradas.
- **Harness de evaluación cuantitativa** del MVP (`app/services/evaluation/`) con métricas y reporte.
- `GET /ai/status` ampliado con el estado y los límites de la capa IA.

### Seguridad
- IA **desactivada por defecto** (`TFG_AI_EXPLANATIONS_ENABLED=false`) y envío del snippet de código al modelo **opt-in** (`TFG_AI_INCLUDE_SNIPPET=false`) por privacidad.

### Calidad
- Suite ampliada a **281 tests** con gate de cobertura al **85%**.
- Cobertura de flujo IA en web (enriquecimiento sin re-SAST), parser tolerante de Ollama y presentable con IA.

## [0.1.0] - 2026-06-10

Primera release: **web de análisis de seguridad operativa, sin IA**.

### Añadido
- Detección con **Bandit** y **Semgrep** sobre proyectos Python con modelo normalizado de hallazgos y clasificación CWE/OWASP/ASVS.
- Análisis de **proyectos reales** desde web y API: subida **ZIP**, **clon Git HTTPS** acotado y **ruta local** bajo directorio permitido.
- **Dashboard** (`/dashboard`) como consola de análisis con modos reales priorizados, vista demo (`hide_info`) y agrupación de equivalentes (`group_equivalent`).
- **Contrato de error unificado** (`error_code`, `message`, `analysis_id`) en API y dashboard.
- **Observabilidad**: `analysis_id` por ejecución y logging estructurado por etapas.
- **Panel de diagnóstico** Bandit/Semgrep en el dashboard (código de salida, hallazgos, vista previa de stderr).
- Pipeline de remediación asistida con verificación en patrones acotados del corpus MVP.
- JSON **presentable** y endpoints de fixtures (estáticos y runtime).
- Endpoint `GET /ai/status` exponiendo flags y límites operativos.

### Seguridad
- Validación reforzada de entradas: firma/tipo/tamaño de ZIP, límites anti zip-bomb, URLs Git (HTTPS, hosts permitidos, longitud), rutas locales (sin `..`, longitud, caracteres de control) y kill-switches (`TFG_ENABLE_GIT_CLONE`, `TFG_ENABLE_LOCAL_PATH`).
- Límites previos al escaneo para árboles muy grandes (ficheros/bytes/exclusiones).

### Calidad
- Linter `ruff` (lint + orden de imports) integrado en CI y `pre-commit`.
- Suite de **170 tests** con gate de cobertura al **85%** (cobertura real ~92%).

[Unreleased]: https://github.com/p3ix/tfg-secure-code-remediation/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/p3ix/tfg-secure-code-remediation/releases/tag/v1.0.0
[0.2.0]: https://github.com/p3ix/tfg-secure-code-remediation/releases/tag/v0.2.0
[0.1.0]: https://github.com/p3ix/tfg-secure-code-remediation/releases/tag/v0.1.0
