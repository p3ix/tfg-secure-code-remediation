### Título

Barrido final de calidad del proyecto sin IA (pre-release)

### Objetivo

Dejar el proyecto compacto, operativo y pulido antes de abordar la integración de la
capa IA. El barrido revisa de forma transversal calidad de código, cobertura de tests,
flujos web extremo a extremo y consistencia documental, sin introducir funcionalidad
nueva ni la IA. Cierra la fase "web operativa sin IA" con garantías reproducibles.

### Tareas

- [x] Incorporar un linter reproducible (`ruff`) con configuración en `pyproject.toml`.
- [x] Corregir los avisos detectados (variable sin uso, imports sin usar, orden de imports).
- [x] Integrar el lint en CI (`.github/workflows/ci.yml`) y en `pre-commit`.
- [x] Reforzar la cobertura del módulo más débil (`runtime_analysis_service.py`) con tests
      de orquestación que no dependen de los binarios reales.
- [x] Elevar el umbral de cobertura del gate de 60 % a 85 % (cobertura real ~92 %).
- [x] Verificar los flujos web extremo a extremo (health, dashboard, `ai/status`, ZIP,
      contrato de error, git-clone, render del dashboard).
- [x] Actualizar documentación (README, memoria) para reflejar el lint y el nuevo umbral.
- [x] Redactar el informe de barrido.

### Criterio de cierre

- [x] `ruff check app tests` sin errores.
- [x] `pytest` en verde con el gate al 85 % (170 tests, ~92 % de cobertura).
- [x] Flujos web validados (validaciones y contrato de error correctos; el único fallo
      observado en sandbox es ambiental —semgrep no puede escribir su log—, no del código).
- [x] Documentación coherente con el estado del repositorio.

### Evidencias

- Informe: [`docs/04_delivery/barrido-final-sin-ia.md`](barrido-final-sin-ia.md)
- Memoria: [`docs/07_memoria/01_evolucion_del_desarrollo.md`](../07_memoria/01_evolucion_del_desarrollo.md) (sección 13)
- Config lint: `pyproject.toml` (`[tool.ruff]`), `.pre-commit-config.yaml`, `.github/workflows/ci.yml`
- Tests añadidos: `tests/test_runtime_analysis_service.py`
