# Alcance inicial del TFG

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

## Alcance del MVP
El MVP se centrará en vulnerabilidades detectables y remediables de forma relativamente fiable, como:
- command injection (`shell=True`, `os.system`)
- uso inseguro de `yaml.load`
- `verify=False` en peticiones HTTPS
- peticiones sin timeout
- `debug=True` en Flask

## Vulnerabilidades inicialmente solo detectables
- SQL injection (detección y propuesta, sin parche automático en MVP)

## Fuera de alcance del MVP
- multilenguaje
- análisis de repositorios remotos
- DAST completo
- parcheo automático de problemas de arquitectura
- integración completa con GitHub PRs
- control de acceso complejo
- XSS y CSRF como autofix inicial

## Supervisión humana
La IA no aplicará cambios de forma ciega: propondrá remediaciones, se validarán y el usuario decidirá si aceptarlas.

## Arquitectura inicial
- backend en FastAPI
- análisis con Bandit y Semgrep
- pruebas con pytest
- documentación y trazabilidad en GitHub
