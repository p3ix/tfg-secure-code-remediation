# Changelog

Todos los cambios relevantes de este proyecto se documentan en este fichero.

El formato sigue, de forma aproximada, [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto usa [Versionado Semántico](https://semver.org/lang/es/).

## [Unreleased]

- Próxima fase: integración de la capa IA de explicación/asistencia (ver `docs/02_decisions/ADR-002-ai-assisted-roadmap.md`).

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

[Unreleased]: https://github.com/p3ix/tfg-secure-code-remediation/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/p3ix/tfg-secure-code-remediation/releases/tag/v0.1.0
