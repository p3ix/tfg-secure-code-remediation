# Tabla de evaluación del corpus MVP

Este documento resume qué hace el sistema con cada categoría del MVP: detección, relación con estándares, remediación asistida, verificación automática y límites conocidos. Sirve como base para la memoria y la defensa.

| Categoría MVP | Herramientas (indicativo) | CWE / OWASP (mapper) | Remediación MVP | Verificación automática | Notas / límites |
|---------------|---------------------------|------------------------|-----------------|-------------------------|-----------------|
| command_injection | Bandit B602/B605, Semgrep shell | CWE-78, A05 Injection, ASVS V1.2 | Sí (subprocess / `os.system` acotados) | Sí (re-análisis) | No cubre todos los vectores; entrada puede seguir influyendo en el comando sin shell |
| unsafe_yaml_load | Bandit B506, reglas yaml Semgrep | CWE-502, A08, ASVS V1.5 | Sí (`safe_load`) | Sí | Patrones simples de `yaml.load` |
| verify_false | Bandit B501, Semgrep TLS | CWE-295, A04, ASVS V12.2 | Sí (`verify=True`) | Sí | Pueden quedar otros hallazgos (p. ej. timeout) en el mismo fichero |
| missing_timeout | Bandit B113, Semgrep timeout | CWE-400 (parcial OWASP) | Sí (`timeout` en `requests`) | Sí | Solo `requests` en MVP; `httpx` distinto por diseño |
| flask_debug_true | Bandit B201, Semgrep debug | CWE-489, A02, ASVS V13 | Sí (`debug=False`) | Sí | No cubre debug por variables de entorno |
| sql_injection | Bandit B608, Semgrep SQL | CWE-89, A05, ASVS V1.2 | No (proposal_only) | No | Detección y clasificación; corrección manual o futura guía textual |

## Criterio de éxito global del MVP

- Flujo **detect → classify → remediate → verify** demostrable para las categorías con autofix, usando el corpus bajo `fixtures/mvp/`.
- Categoría SQL injection acotada a **detección y propuesta**, coherente con el alcance.
- Resultados visibles vía API y vista web mínima (`/dashboard`) además del JSON presentable.
