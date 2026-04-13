# Alcance del TFG

## Título provisional
Aplicación web para análisis y remediación asistida por IA de vulnerabilidades en proyectos Python.

## Objetivo general
Desarrollar una aplicación web capaz de analizar proyectos Python, detectar vulnerabilidades de seguridad relevantes, relacionarlas con estándares reconocidos y proponer correcciones cuando sea viable, manteniendo supervisión humana sobre los cambios.

## Enfoque
El flujo principal será:
1. detección,
2. propuesta de remediación,
3. verificación posterior,
4. presentación del resultado al usuario.

## Lenguaje objetivo
Python.

## Alcance del MVP (fixtures y corpus controlado)
El núcleo inicial se valida sobre **fixtures** bajo `fixtures/mvp/`, con vulnerabilidades detectables y remediables de forma relativamente fiable, como:
- command injection (`shell=True`, `os.system`)
- uso inseguro de `yaml.load`
- `verify=False` en peticiones HTTPS
- peticiones sin timeout
- `debug=True` en Flask

## Vulnerabilidades inicialmente solo detectables
- SQL injection (detección y propuesta, sin parche automático en MVP)

## Ampliación — Fase “proyectos reales” (en curso / siguiente iteración)
Además del corpus interno, el sistema puede analizar **código real** suministrado como:

- **Archivo ZIP** subido por API (`POST /analysis/upload-zip`), con límites de tamaño y extracción segura (sin path traversal).
- **Repositorio Git HTTPS** clonado de forma superficial (`POST /analysis/git-clone`), con hosts permitidos por configuración (`TFG_GIT_ALLOWED_HOSTS`), timeout y **solo en entornos de confianza** (el clonado puede desactivarse con `TFG_ENABLE_GIT_CLONE=0`).

Riesgos y límites (licencias, datos sensibles, tiempo de análisis) deben documentarse en la memoria y, si aplica, en issues de seguridad.

## Ampliación — IA (roadmap)
- Explicación de hallazgos o sugerencias de parche mediante modelo **opcional**, desactivado por defecto (`TFG_AI_EXPLANATIONS_ENABLED`).
- Criterios de supervisión humana y referencia normativa: ver [`docs/02_decisions/ADR-002-ai-assisted-roadmap.md`](02_decisions/ADR-002-ai-assisted-roadmap.md).

## Fuera de alcance (MVP estricto inicial)
- multilenguaje
- DAST completo
- parcheo automático de problemas de arquitectura
- integración completa con GitHub PRs
- control de acceso complejo
- XSS y CSRF como autofix inicial

**Nota:** El análisis de repositorios remotos vía Git **sí** entra en la ampliación de fase descrita arriba; la exclusión original se reinterpreta como “sin analizar repos arbitrarios *sin* controles de seguridad y límites explícitos”.

## Supervisión humana
La IA no aplicará cambios de forma ciega: propondrá remediaciones, se validarán y el usuario decidirá si aceptarlas.

## Arquitectura inicial
- backend en FastAPI
- análisis con Bandit y Semgrep
- pruebas con pytest
- documentación y trazabilidad en GitHub

## Planificación y ritual de documentación
Ver [`docs/01_roadmap_and_documentation_ritual.md`](01_roadmap_and_documentation_ritual.md).
