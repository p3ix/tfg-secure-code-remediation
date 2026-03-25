# Mapeo inicial de hallazgos a CWE, OWASP Top 10 y ASVS

## 1. Objetivo

En este documento defino un mapeo inicial para enriquecer los hallazgos normalizados del sistema con referencias a CWE, OWASP Top 10 y OWASP ASVS.

El objetivo de este paso es que el sistema no se limite a mostrar el resultado nativo de Bandit o Semgrep, sino que pueda contextualizar los hallazgos dentro de marcos reconocidos en ciberseguridad. Esta capa de clasificación es útil tanto para el funcionamiento interno del sistema como para la documentación y defensa del TFG.

## 2. Criterio adoptado

He decidido utilizar un criterio simple y determinista basado en `mvp_category`.

La razón es que, en esta fase del proyecto, ya existe una categorización funcional suficientemente estable para los casos del MVP:
- `command_injection`
- `unsafe_yaml_load`
- `verify_false`
- `missing_timeout`
- `flask_debug_true`
- `sql_injection`

A partir de esta categoría, el sistema asigna una clasificación primaria del proyecto. Esta clasificación no pretende sustituir completamente el resultado original de la herramienta, sino añadir una interpretación propia, estable y útil para el flujo del TFG.

Por este motivo:
- el hallazgo original se conserva;
- la información cruda de la herramienta sigue disponible;
- y el sistema añade una clasificación primaria propia para trabajar de forma uniforme.

## 3. Tabla de mapeo inicial

| MVP category | CWE primario | OWASP Top 10 | ASVS | Tipo de mapeo |
|---|---|---|---|---|
| `command_injection` | CWE-78 | A05:2025 Injection | ASVS v5.0.0 V1.2 Injection Prevention | Fuerte |
| `unsafe_yaml_load` | CWE-502 | A08:2025 Software or Data Integrity Failures | ASVS v5.0.0 V1.5 Safe Deserialization | Fuerte |
| `verify_false` | CWE-295 | A04:2025 Cryptographic Failures | ASVS v5.0.0 V12.2 HTTPS Communication with External Facing Services | Fuerte |
| `missing_timeout` | CWE-400 | Sin asignación inicial | Sin asignación inicial | Provisional |
| `flask_debug_true` | CWE-489 | A02:2025 Security Misconfiguration | ASVS v5.0.0 V13 Configuration | Fuerte |
| `sql_injection` | CWE-89 | A05:2025 Injection | ASVS v5.0.0 V1.2 Injection Prevention | Fuerte |

## 4. Nota importante sobre el carácter “primario” del mapeo

En algunos casos, la clasificación primaria del proyecto puede no coincidir exactamente con la referencia devuelta por una herramienta concreta.

Por ejemplo, un hallazgo relacionado con `yaml.load` puede venir acompañado por una referencia técnica distinta según la herramienta, pero en el sistema se decide clasificarlo primariamente bajo una categoría estable del proyecto para facilitar:
- la uniformidad del tratamiento;
- la trazabilidad documental;
- la posterior remediación;
- y la comparación entre herramientas.

La referencia original de la herramienta no se pierde, ya que se conserva en la información cruda asociada al hallazgo.

## 5. Caso provisional: `missing_timeout`

He decidido tratar `missing_timeout` como un caso de clasificación provisional.

En esta primera iteración:
- se conserva CWE-400 como referencia de trabajo;
- no se fuerza todavía una asignación OWASP Top 10;
- no se fuerza todavía una asignación ASVS.

Esta decisión busca evitar un mapeo artificialmente fuerte en un caso donde el encaje conceptual puede depender mucho del contexto del sistema y de la política técnica adoptada.
