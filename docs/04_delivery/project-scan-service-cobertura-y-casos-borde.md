# Avance: cobertura y casos borde de `project_scan_service`

## Objetivo del avance

Reforzar la confiabilidad del servicio de escaneo de proyectos reales (`project_scan_service`) cubriendo rutas de error críticas que pueden aparecer en producción, sin ampliar alcance funcional.

## Cambios realizados

Archivo principal de pruebas: `tests/test_project_scan_service.py`

Se añadieron pruebas para escenarios de robustez:

- `analyze_directory` con ruta no-directorio.
- `analyze_directory` cuando Bandit no genera informe.
- `analyze_directory` cuando Semgrep no genera informe.
- validación de `resolve_allowed_analysis_path` con espacios inválidos.
- `analyze_local_path_relative` con subruta inexistente.
- `clone_and_analyze_repo` con clonado incompleto (returncode 0 pero sin directorio de repo).

## Valor técnico

- Mejora la detección de fallos operativos silenciosos.
- Asegura mensajes de error coherentes y accionables en flujos reales.
- Reduce riesgo de regresiones en zonas con alta complejidad de E/S y subprocess.

## Evidencia de validación

Comando ejecutado:

- `.venv/bin/pytest -q`

Resultado:

- `131 passed`
- cobertura global: `91.22%`
- cobertura de `app/services/project_scan_service.py`: `83%`

## Conclusión

El servicio mantiene su comportamiento funcional, pero con mayor robustez comprobada en ramas borde de directorio, informes de herramientas y clonado remoto.
