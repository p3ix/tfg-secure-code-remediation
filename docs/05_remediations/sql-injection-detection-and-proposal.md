# SQL injection: detección y propuesta sin autofix

## Objetivo

Documentar el tratamiento del caso de SQL injection dentro del MVP como categoría de solo detección y propuesta textual, sin remediación automática.

## Decisión adoptada

A diferencia de los otros cinco casos del MVP, SQL injection se clasifica como `proposal_only` y no como `autofix_candidate`. Esto significa que el sistema detecta el hallazgo, lo clasifica con CWE/OWASP y lo presenta al usuario, pero no genera un parche automático.

## Justificación

Las remediaciones de SQL injection dependen fuertemente del contexto:

- la consulta puede estar construida con f-strings, concatenación, `.format()` u otras formas;
- la corrección puede requerir usar consultas parametrizadas, ORMs o funciones de escape, según el caso;
- aplicar un parche genérico podría romper lógica de negocio o introducir errores difíciles de detectar.

Por estos motivos, un autofix conservador y verificable no es viable en esta primera versión sin asumir riesgos que no encajan con la filosofía del TFG.

## Qué hace el sistema con este caso

- Bandit (B608) y Semgrep detectan el patrón en el fixture `vuln_sql_injection.py`.
- Los parsers lo clasifican como `mvp_category="sql_injection"` con `remediation_mode="proposal_only"`.
- El mapper lo enriquece con CWE-89, OWASP A05:2025 (Injection) y ASVS V1.2.
- El usuario recibe el hallazgo clasificado y contextualizado, pero la decisión de cómo corregirlo queda en sus manos.

## Limitaciones

- No se genera propuesta de código alternativo.
- No se ejecuta verificación automatizada para este caso.
- En una ampliación futura se podría proponer texto orientativo (por ejemplo, "considerar consultas parametrizadas"), pero eso queda fuera del alcance actual.
