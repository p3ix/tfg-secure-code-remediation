# Marco teórico y estado del arte

Este capítulo resume los conceptos y referencias en los que se apoya el TFG: marcos de clasificación de riesgos (OWASP, CWE), verificación de controles (ASVS), prácticas de desarrollo seguro (NIST SSDF), análisis estático (*SAST*) y el encaje del flujo **detect → repair → verify** con supervisión humana. Las fuentes bibliográficas detalladas están catalogadas en [`docs/06_references/README.md`](../06_references/README.md) con identificadores **[REF-xxx]**; aquí se usa esa numeración para mantener trazabilidad con la memoria final.

El capítulo es **complementario** al de [evolución del desarrollo](01_evolucion_del_desarrollo.md): allí se narra *qué se hizo* en el proyecto; aquí se expone *en qué marco conceptual* encaja.

---

## 1. Seguridad en el ciclo de vida del software

La idea de integrar la seguridad de forma temprana —a veces resumida como “*shift left*” o enfoques tipo *DevSecOps*— responde a que corregir defectos en fases tardías suele ser más costoso y arriesgado. Los organismos de normalización y buenas prácticas publican marcos que no sustituyen el criterio del desarrollador, pero sí ofrecen **lenguaje común** y **listas de comprobación** útiles para diseño, implementación y revisión.

En este TFG adopté como referencia general el **NIST Secure Software Development Framework (SSDF)** [REF-016], que organiza prácticas recomendables alrededor de preparar la organización, proteger el software y producir artefactos bien resguardados. No implemento el SSDF al completo (sería inviable en un MVP de Grado), pero sí justifica la coherencia del enfoque: **analizar** el código, **producir** evidencias trazables y **no confiar** ciegamente en automatismos sin verificación. Cuando se menciona supervisión humana o prudencia ante la IA, la publicación complementaria [REF-017] aporta marco para no presentar la remediación asistida como sustituto del juicio experto.

---

## 2. Taxonomías de debilidades y riesgos en aplicaciones

### 2.1. CWE y la CWE Top 25

**Common Weakness Enumeration (CWE)** es un catálogo de tipos de debilidades en software; permite hablar de “inyección” o “deserialización insegura” con definiciones estables. La **CWE Top 25** [REF-015] destaca debilidades que, por frecuencia y gravedad, suelen asociarse a impacto relevante. En el proyecto, cada categoría MVP se enlaza con un **CWE primario** cuando el encaje es defendible (véase [`docs/01_findings_classification_mapping.md`](../01_findings_classification_mapping.md)): por ejemplo inyección de comandos con **CWE-78**, SQL injection con **CWE-89**, deserialización insegura de `yaml.load` con **CWE-502**, verificación TLS desactivada con **CWE-295**.

Conviene insistir en que CWE describe **debilidades**, no incidentes concretos: el mismo CWE puede manifestarse de formas distintas según el contexto.

### 2.2. OWASP Top 10

El **OWASP Top 10** [REF-014] resume categorías de riesgo frecuentes en aplicaciones web (la edición vigente en el momento del trabajo es la de 2025). Sirve para **contextualizar** hallazgos ante perfiles no especializados y para alinear el discurso del TFG con un documento muy citado en la industria. En la implementación, el mapeo desde `mvp_category` a entradas del Top 10 es **determinista** (por ejemplo inyecciones bajo **A05:2025 Injection**, fallos de integridad relacionados con deserialización bajo **A08:2025**, etc.), tal como figura en la tabla del documento de mapeo.

### 2.3. OWASP ASVS

El **Application Security Verification Standard (ASVS)** [REF-013] describe requisitos verificables para la seguridad de aplicaciones, organizados por capítulos (autenticación, comunicación, configuración, etc.). En el MVP lo uso como **capa de referencia opcional pero valiosa**: cuando un hallazgo encaja con un requisito ASVS (por ejemplo controles de inyección o configuración segura), el sistema puede mostrar esa asociación. No pretendo una auditoría ASVS completa del código analizado; sí demostrar que el diseño **no es aislado**, sino conectable a un estándar de verificación reconocido.

---

## 3. Análisis estático de seguridad (SAST) y herramientas del MVP

El análisis estático examina el código (o representaciones derivadas) sin ejecutar la aplicación completa frente a un entorno de producción. Tiene **ventajas**: escalabilidad, integración en CI, detección temprana de patrones peligrosos. Tiene también **limitaciones**: falsos positivos, falsos negativos, avisos informativos que no equivalen a una vulnerabilidad explotable, y dificultad para razonar sobre todo el flujo de datos sin análisis más profundo.

En este trabajo se integran dos herramientas de ámbito práctico ampliamente documentadas:

- **Bandit** [REF-008]–[REF-011], orientada a Python y a tests heurísticos concretos, con salida estructurada en JSON [REF-011].
- **Semgrep** [REF-012], con reglas y motor que permiten cubrir patrones de forma declarativa y complementar a Bandit.

La decisión de usar **dos** analizadores no implica que sean redundantes en todos los casos: en la práctica aparece **solapamiento** y también **complemento**; por eso el backend introduce un modelo normalizado y documentación sobre ruido y duplicados ([`docs/04_delivery/scan-noise-and-duplicates.md`](../04_delivery/scan-noise-and-duplicates.md)).

---

## 4. Del hallazgo a la mejora: detectar, remediar y verificar

Un informe SAST por sí solo no “arregla” el software: hace falta un **ciclo** que muchos equipos resumen como detectar → corregir → validar. En este TFG lo formalizo como **detect → repair → verify**:

1. **Detect**: Bandit y Semgrep producen hallazgos; los parsers los proyectan a un modelo común (`NormalizedFinding`).
2. **Repair (asistido)**: para categorías con remediación automática acotada, el sistema propone un cambio conservador sobre una copia de trabajo; el usuario mantiene la decisión final ([`docs/00_scope.md`](../00_scope.md)).
3. **Verify**: se vuelve a ejecutar el análisis relevante y se comprueba que el aviso objetivo desaparece o cumple el criterio definido en tests.

Este ciclo es defendible frente al tribunal: combina **automatización** con **límites explícitos** (por ejemplo SQL injection solo como detección y propuesta textual en el MVP). La verificación automática no sustituye pruebas de penetración ni revisión humana sistemática; reduce el riesgo de que una “corrección” deje el mismo patrón detectable por las reglas usadas.

---

## 5. Relación con el trabajo implementado

La siguiente tabla resume cómo el marco teórico anterior se **materializa** en artefactos del repositorio (sin repetir la narrativa de implementación del capítulo de evolución):

| Concepto teórico | Uso en el proyecto |
|--------------------|---------------------|
| CWE / OWASP / ASVS | Mapeo por `mvp_category` en [`docs/01_findings_classification_mapping.md`](../01_findings_classification_mapping.md) |
| SAST (Bandit, Semgrep) | Integración documentada en `docs/03_experiments/`, parsers y cargador unificado |
| Ciclo detect–repair–verify | Remediadores, verificadores, orquestador (`docs/03_experiments/pipeline-orchestrator.md`) |
| Supervisión humana | Alcance y modos `remediation_mode` en modelo normalizado y [`docs/00_scope.md`](../00_scope.md) |
| Ruido y duplicados | [`docs/04_delivery/scan-noise-and-duplicates.md`](../04_delivery/scan-noise-and-duplicates.md) |
| Evaluación del MVP (memoria) | [Capítulo 04](04_resultados_y_evaluacion_del_mvp.md) |

---

## 6. Trabajos relacionados y límites de este capítulo

Existen numerosas plataformas comerciales y proyectos de código abierto que combinan SAST, gestión de hallazgos y, en algunos casos, remediación asistida por modelos generativos. Una comparación exhaustiva excede el alcance de este capítulo; el aporte del TFG es **acotado y trazable**: un MVP documentado, reproducible desde el repositorio, con decisiones explícitas sobre alcance y verificación.

Para la bibliografía detallada y futuras ampliaciones, conviene partir de [`docs/06_references/README.md`](../06_references/README.md) y completar la memoria final con las citas en formato exigido por el centro docente.

---

## Referencias cruzadas

- Catálogo de referencias [REF-001]–[REF-018]: [`docs/06_references/README.md`](../06_references/README.md)
- Mapeo de hallazgos: [`docs/01_findings_classification_mapping.md`](../01_findings_classification_mapping.md)
- Introducción y estructura de la memoria: [`docs/07_memoria/02_introduccion_y_estructura_de_la_memoria.md`](02_introduccion_y_estructura_de_la_memoria.md)
- Resultados y evaluación del MVP: [`docs/07_memoria/04_resultados_y_evaluacion_del_mvp.md`](04_resultados_y_evaluacion_del_mvp.md)
- Conclusiones y trabajo futuro: [`docs/07_memoria/05_conclusiones_y_trabajo_futuro.md`](05_conclusiones_y_trabajo_futuro.md)
- Evolución del desarrollo: [`docs/07_memoria/01_evolucion_del_desarrollo.md`](01_evolucion_del_desarrollo.md)

---

*Texto elaborado como borrador de memoria del TFG, alineado con el estado del repositorio en el momento de su redacción.*
