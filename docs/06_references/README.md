# Referencias técnicas y bibliográficas del TFG

## Objetivo de este directorio

En este directorio recopilo las referencias técnicas, normativas y bibliográficas que voy utilizando durante el desarrollo del TFG. El objetivo es conservar trazabilidad de las fuentes empleadas para justificar decisiones de arquitectura, herramientas, metodología, seguridad, validación y evaluación.

Siempre que sea posible, priorizo:
1. documentación oficial,
2. estándares reconocidos,
3. publicaciones técnicas de organismos o proyectos de referencia,
4. trabajos relacionados cuando aporten valor comparativo.

---

## Gestión del proyecto y trazabilidad

### [REF-001] GitHub Issues
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar el uso de issues como unidades de trabajo trazables
- **Referencia**: GitHub Docs — About issues
- **Enlace**: https://docs.github.com/articles/about-issues
- **Nota**: útil para explicar el papel de las issues dentro del proceso de desarrollo

### [REF-002] GitHub Projects
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar el uso del tablero de planificación y seguimiento
- **Referencia**: GitHub Docs — About Projects
- **Enlace**: https://docs.github.com/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects
- **Nota**: útil para describir la organización del trabajo por sprints y estados

### [REF-003] GitHub Releases
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar el uso de releases como hitos del proyecto
- **Referencia**: GitHub Docs — About releases
- **Enlace**: https://docs.github.com/repositories/releasing-projects-on-github/about-releases
- **Nota**: útil para documentar versiones y entregas intermedias

### [REF-004] GitHub Actions
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar la integración continua básica
- **Referencia**: GitHub Docs — GitHub Actions documentation
- **Enlace**: https://docs.github.com/actions
- **Nota**: útil para explicar la validación automática del repositorio

---

## Stack base del proyecto

### [REF-005] FastAPI
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar la elección del backend
- **Referencia**: FastAPI Documentation — First Steps
- **Enlace**: https://fastapi.tiangolo.com/tutorial/first-steps/
- **Nota**: útil para justificar la estructura inicial del backend y la creación de endpoints

### [REF-006] pytest
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar la estrategia de testing
- **Referencia**: pytest documentation — Get Started
- **Enlace**: https://docs.pytest.org/en/stable/getting-started.html
- **Nota**: útil para describir la ejecución de pruebas y el uso general de pytest

### [REF-007] pytest fixtures
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar el uso del concepto de fixtures y bases reproducibles de prueba
- **Referencia**: pytest documentation — About fixtures
- **Enlace**: https://docs.pytest.org/en/stable/explanation/fixtures.html
- **Nota**: útil para relacionar el corpus de ejemplos vulnerables con la futura validación

---

## Herramientas de análisis de seguridad

### [REF-008] Bandit
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar Bandit como herramienta SAST para Python
- **Referencia**: Bandit documentation — Welcome to Bandit
- **Enlace**: https://bandit.readthedocs.io/
- **Nota**: describe Bandit como herramienta para encontrar problemas comunes de seguridad en código Python

### [REF-009] Bandit getting started
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar instalación, ejecución recursiva y uso inicial
- **Referencia**: Bandit documentation — Getting Started
- **Enlace**: https://bandit.readthedocs.io/en/latest/start.html
- **Nota**: útil para documentar la integración inicial de Bandit en el proyecto

### [REF-010] Bandit configuration
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar configuración mediante `pyproject.toml`
- **Referencia**: Bandit documentation — Configuration
- **Enlace**: https://bandit.readthedocs.io/en/latest/config.html
- **Nota**: útil para documentar exclusiones, selección de tests y configuración del análisis

### [REF-011] Bandit JSON formatter
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar el almacenamiento estructurado de resultados
- **Referencia**: Bandit documentation — JSON formatter
- **Enlace**: https://bandit.readthedocs.io/en/latest/formatters/json.html
- **Nota**: útil para guardar y procesar resultados de análisis

### [REF-012] Semgrep Community Edition
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar Semgrep CE como herramienta complementaria de análisis
- **Referencia**: Semgrep Docs — OSS deployment / Semgrep Community Edition in CI
- **Enlace**: https://semgrep.dev/docs/deployment/oss-deployment
- **Nota**: útil para la integración posterior de Semgrep en el proyecto

---

## Estándares y marcos de referencia

### [REF-013] OWASP ASVS
- **Tipo**: estándar / proyecto oficial
- **Uso en el TFG**: justificar la verificación y contextualización de controles
- **Referencia**: OWASP Application Security Verification Standard (ASVS)
- **Enlace**: https://owasp.org/www-project-application-security-verification-standard/
- **Nota**: útil como marco para relacionar controles y requisitos de seguridad

### [REF-014] OWASP Top 10
- **Tipo**: referencia oficial
- **Uso en el TFG**: contextualizar riesgos de seguridad en aplicaciones web
- **Referencia**: OWASP Top 10:2025
- **Enlace**: https://owasp.org/Top10/2025/
- **Nota**: útil para el marco teórico y la clasificación de hallazgos

### [REF-015] CWE Top 25
- **Tipo**: referencia oficial MITRE
- **Uso en el TFG**: contextualizar debilidades frecuentes y peligrosas
- **Referencia**: CWE Top 25 Most Dangerous Software Weaknesses
- **Enlace**: https://cwe.mitre.org/top25/
- **Nota**: útil para enlazar vulnerabilidades con debilidades reconocidas

### [REF-016] NIST SSDF
- **Tipo**: publicación oficial
- **Uso en el TFG**: justificar el marco metodológico general de desarrollo seguro
- **Referencia**: NIST SP 800-218 — Secure Software Development Framework (SSDF) Version 1.1
- **Enlace**: https://csrc.nist.gov/pubs/sp/800/218/final
- **Nota**: útil para justificar buenas prácticas de desarrollo seguro

### [REF-017] NIST SP 800-218A
- **Tipo**: publicación oficial
- **Uso en el TFG**: apoyar la discusión sobre IA y desarrollo seguro
- **Referencia**: Secure Software Development Practices for Generative AI and Dual-Use Foundation Models
- **Enlace**: https://csrc.nist.gov/pubs/sp/800/218/a/final
- **Nota**: útil para justificar prudencia, supervisión humana y verificación cuando interviene IA

---

## Licencias

### [REF-018] GitHub licensing a repository
- **Tipo**: documentación oficial
- **Uso en el TFG**: justificar la inclusión explícita de licencia en el repositorio
- **Referencia**: GitHub Docs — Licensing a repository
- **Enlace**: https://docs.github.com/articles/licensing-a-repository
- **Nota**: útil para el apartado legal y de reutilización del software

---

## Criterio de mantenimiento

Este directorio se irá actualizando a medida que avance el proyecto. Cada vez que se incorpore una herramienta, estándar o fuente relevante para justificar una decisión técnica, metodológica o de evaluación, se añadirá aquí con su identificador correspondiente.
