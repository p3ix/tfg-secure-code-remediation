# TFG Secure Code Remediation

Aplicación web para análisis y remediación asistida por IA de vulnerabilidades en proyectos Python, especialmente aplicaciones web.

## Objetivo
Permitir que un usuario suba un proyecto Python para:
- detectar vulnerabilidades relevantes,
- mapearlas a estándares de seguridad,
- proponer remediaciones cuando sea viable,
- y verificar el resultado antes de aceptarlo.

## Stack inicial
- Python 3.12
- FastAPI
- pytest
- Bandit
- Semgrep
- pre-commit

## Estado
Fase inicial de preparación del entorno y arquitectura base.

## Ejecución local
```bash
uvicorn app.main:app --reload
```
