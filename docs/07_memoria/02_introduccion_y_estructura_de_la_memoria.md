# Introducción y estructura de la memoria

Este capítulo sitúa el trabajo en su contexto, expone la motivación y los objetivos, y describe cómo está organizada la memoria que acompaña al desarrollo realizado en el repositorio. Complementa al capítulo de [evolución del desarrollo](01_evolucion_del_desarrollo.md), donde se narra con más detalle el proceso, las decisiones y las dificultades técnicas.

---

## 1. Contexto y motivación

La seguridad del software ha dejado de ser un añadido opcional en proyectos reales: vulnerabilidades conocidas, configuraciones inseguras y malas prácticas en el código se traducen con frecuencia en incidentes, fugas de datos y costes elevados de remediación tardía. En entornos de desarrollo ágil, integrar la seguridad de forma temprana en el ciclo de vida (ideas cercanas a *DevSecOps* y a “*shift left*”) es un objetivo compartido por la industria y por buena parte de la literatura especializada.

En el caso concreto de **Python**, el ecosistema ofrece librerías muy productivas, pero también patrones que, mal usados, generan riesgos claros: deserialización insegura, desactivación de la verificación TLS, opciones de depuración activas en producción, ausencia de límites temporales en peticiones de red o concatenación de comandos de sistema. Herramientas de análisis estático (*SAST*) como **Bandit** o **Semgrep** ayudan a detectar parte de esos problemas, pero sus informes suelen ser heterogéneos, a veces ruidosos, y no cierran por sí solos el ciclo de mejora: hace falta **interpretación**, **priorización** y, cuando procede, **remediación** acotada y **verificación** posterior.

La motivación de este TFG es doble. Por un lado, **académica**: demostrar comprensión del problema, del estado del arte práctico (OWASP, CWE, ASVS donde aplique) y de un diseño de software defendible. Por otro, **ingenieril**: construir un **producto mínimo viable** que integre detección con dos herramientas, una capa de hallazgos normalizados y clasificados, remediación asistida con verificación automática en casos acotados, y presentación del resultado al usuario, **sin** sustituir el juicio humano ni prometer correcciones universales.

---

## 2. Objetivos

### 2.1. Objetivo general

Desarrollar una **aplicación web** orientada a proyectos **Python**, capaz de:

1. **Analizar** código (en el alcance del MVP, principalmente mediante análisis estático con Bandit y Semgrep).
2. **Detectar** vulnerabilidades o malas prácticas relevantes y **relacionarlas** con estándares reconocidos (por ejemplo CWE, OWASP Top 10, ASVS en la medida en que el mapeo sea razonable y trazable).
3. **Proponer remediaciones** cuando sea técnicamente viable y seguro hacerlo de forma conservadora, y **verificar** en la medida posible que el aviso objetivo desaparece tras la propuesta.
4. **Presentar** los resultados de forma clara (incluido un JSON orientado a demostración y un dashboard HTML en el MVP), manteniendo la **supervisión humana** sobre la aceptación de cambios.

Este objetivo general está alineado con el documento de [alcance del proyecto](../00_scope.md).

### 2.2. Objetivos específicos

Los objetivos específicos que he perseguido en el marco del MVP son:

- Definir un **modelo normalizado de hallazgos** independiente del formato nativo de Bandit y Semgrep, con categorías MVP y modos de remediación explícitos.
- Implementar **parsers**, un **cargador unificado** y un **mapeo** a taxonomías comunes, de forma **determinista** y documentada.
- Integrar **remediación asistida** y **verificación automática** para un conjunto acotado de patrones (por ejemplo `yaml.load` inseguro, `verify=False`, `debug=True` en Flask, ausencia de `timeout` en `requests`, patrones de command injection reconocibles), y limitar **SQL injection** a detección y propuesta sin parche automático general en el MVP.
- Proveer un **orquestador** del flujo detect → classify → verify y una **salida presentable**, junto con **documentación** de entrega y de fenómenos como duplicados entre herramientas o hallazgos meramente informativos.
- Mantener **trazabilidad** del desarrollo (issues, PRs, documentación en `docs/`) coherente con la metodología descrita en [Metodología y planificación](../01_methodology_and_planning.md).

---

## 3. Enfoque y límites del trabajo

El enfoque principal del MVP es el flujo **detect → repair → verify**, con énfasis en la **reproducibilidad** y en la **reducción del alcance** frente a soluciones “mágicas”. No se pretende:

- cubrir **multilenguaje** ni sustituir a un equipo de seguridad;
- realizar **DAST** completo ni analizar repositorios remotos de terceros sin un diseño de confianza y legalidad que excede este TFG;
- aplicar **IA generativa** que reescriba proyectos enteros sin control;
- garantizar ausencia total de vulnerabilidades: el análisis estático y las remediaciones puntuales **reducen riesgo** en los patrones cubiertos, pero no certifican seguridad global.

Estos límites están razonados en el alcance y se reflejan en las decisiones narradas en el capítulo de evolución del desarrollo.

---

## 4. Estructura prevista de la memoria

La memoria final que presente ante el tribunal no será una copia literal de todo el contenido de `docs/`, pero sí se apoyará en él. La estructura que contemplo es la siguiente:

| Orden previsto | Contenido | Relación con el repositorio |
|----------------|-----------|-----------------------------|
| Resumen / abstract | Síntesis del problema, método y resultados | Nuevo texto breve |
| Introducción | Contexto, motivación, objetivos, estructura del documento | Este capítulo y ampliación formal |
| Estado del arte y marco teórico | OWASP, CWE, ASVS, SAST, pipelines de remediación | [Capítulo 03](03_marco_teorico_y_estado_del_arte.md); [`docs/06_references/README.md`](../06_references/README.md) |
| Requisitos y alcance | Qué se hace y qué no | [`docs/00_scope.md`](../00_scope.md) |
| Metodología | Planificación, herramientas, trazabilidad | [`docs/01_methodology_and_planning.md`](../01_methodology_and_planning.md); [`docs/01_roadmap_and_documentation_ritual.md`](../01_roadmap_and_documentation_ritual.md) |
| Diseño e implementación | Arquitectura, modelo de datos, API, remediaciones | [`docs/01_architecture_overview.md`](../01_architecture_overview.md), modelo normalizado, `docs/05_remediations/` |
| Evolución del desarrollo | Decisiones, hitos, dificultades | [Capítulo 01](01_evolucion_del_desarrollo.md) |
| Resultados y evaluación | Tablas de evaluación MVP, limitaciones | [Capítulo 04](04_resultados_y_evaluacion_del_mvp.md); [`docs/04_delivery/mvp-evaluation-table.md`](../04_delivery/mvp-evaluation-table.md) |
| Conclusiones y trabajo futuro | Lecciones aprendidas, líneas abiertas | [Capítulo 05](05_conclusiones_y_trabajo_futuro.md) |
| Roadmap por fases y cadencia de memoria | Cómo se actualiza la memoria durante el curso | [Capítulo 06](06_roadmap_fases_y_cadencia_memoria.md) |
| Bibliografía y anexos | Referencias, capturas, extractos de issues | Repo y material de apoyo |

Los capítulos de documentación técnica en `docs/` sirven como **fuente de verdad** durante el desarrollo; la memoria **prioriza la narrativa** y la argumentación frente al tribunal, citando o resumiendo lo que aquí ya está detallado.

---

## 5. Relación entre este capítulo y el de evolución del desarrollo

- En **[Introducción y estructura de la memoria](02_introduccion_y_estructura_de_la_memoria.md)** (este documento) fijo el **marco**: por qué el proyecto existe, hacia dónde apunta y cómo se organizará la memoria escrita.
- En **[Evolución del desarrollo, decisiones y dificultades](01_evolucion_del_desarrollo.md)** desarrollo la **cronología lógica** del trabajo en el repositorio, enlazada con las issues y con la documentación de experimentos y entrega.

Recomiendo al lector del repositorio seguir primero la introducción si busca **motivación y objetivos**, el capítulo de [marco teórico y estado del arte](03_marco_teorico_y_estado_del_arte.md) si busca **fundamentos OWASP/CWE/ASVS y encaje del SAST** con el proyecto, el capítulo de [resultados y evaluación del MVP](04_resultados_y_evaluacion_del_mvp.md) si busca **criterios de éxito, síntesis por categoría y limitaciones** de la evaluación, el capítulo de [conclusiones y trabajo futuro](05_conclusiones_y_trabajo_futuro.md) si busca **cierre argumental y líneas abiertas**, el capítulo de [roadmap y cadencia de memoria](06_roadmap_fases_y_cadencia_memoria.md) si busca **cómo se encadenan fases técnicas y actualización de la memoria**, y el capítulo de evolución si busca **qué se hizo en cada fase** y con qué problemas nos encontramos.

---

## Referencias cruzadas

- Alcance: [`docs/00_scope.md`](../00_scope.md)
- Metodología y planificación: [`docs/01_methodology_and_planning.md`](../01_methodology_and_planning.md)
- Arquitectura: [`docs/01_architecture_overview.md`](../01_architecture_overview.md)
- Marco teórico y estado del arte: [`docs/07_memoria/03_marco_teorico_y_estado_del_arte.md`](03_marco_teorico_y_estado_del_arte.md)
- Resultados y evaluación del MVP: [`docs/07_memoria/04_resultados_y_evaluacion_del_mvp.md`](04_resultados_y_evaluacion_del_mvp.md)
- Conclusiones y trabajo futuro: [`docs/07_memoria/05_conclusiones_y_trabajo_futuro.md`](05_conclusiones_y_trabajo_futuro.md)
- Roadmap y cadencia de memoria: [`docs/07_memoria/06_roadmap_fases_y_cadencia_memoria.md`](06_roadmap_fases_y_cadencia_memoria.md)
- Evolución del desarrollo: [`docs/07_memoria/01_evolucion_del_desarrollo.md`](01_evolucion_del_desarrollo.md)

---

*Texto elaborado como borrador de memoria del TFG*
