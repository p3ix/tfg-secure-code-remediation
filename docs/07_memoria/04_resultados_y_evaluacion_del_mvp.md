# Resultados y evaluación del MVP

Este capítulo resume **qué se ha logrado** respecto a los objetivos fijados en el [alcance](../00_scope.md) y en la [introducción](02_introduccion_y_estructura_de_la_memoria.md), y **cómo se valora** ese logro. No sustituye la tabla técnica de [`docs/04_delivery/mvp-evaluation-table.md`](../04_delivery/mvp-evaluation-table.md), donde está el detalle tabular por categoría; aquí se ofrece la **lectura en prosa** para la memoria y la defensa. Las **conclusiones finales** y el **trabajo futuro** quedan para un capítulo posterior.

---

## 1. Qué se entiende por “resultados” en este TFG

En un trabajo de ingeniería con un MVP acotado, los resultados no se presentan como un experimento estadístico de gran escala sobre miles de repositorios reales. El diseño adoptado es deliberadamente **cualitativo y verificable**:

- un **corpus de fixtures** bajo `fixtures/mvp/`, representativo de patrones concretos;
- **herramientas SAST** (Bandit y Semgrep) integradas y comparables a través de un modelo normalizado;
- **remediación asistida** y **verificación automática** donde el alcance lo permite, con pruebas que respaldan el comportamiento;
- **presentación** de resultados vía API, JSON presentable y dashboard HTML.

Evaluar el MVP consiste, por tanto, en comprobar si esos elementos funcionan de forma **coherente** con el alcance y si el flujo **detect → classify → remediate → verify** es **demostrable** de extremo a extremo para las categorías con autofix.

---

## 2. Criterio de éxito global

Tomando como base el documento de entrega, el criterio de éxito global del MVP puede resumirse así:

1. El flujo **detect → classify → remediate → verify** debe ser **demostrable** para las categorías con remediación automática en el corpus `fixtures/mvp/`.
2. La categoría **SQL injection** debe permanecer acotada a **detección y propuesta** (`proposal_only`), coherente con el riesgo de parches automáticos genéricos.
3. Los resultados deben ser **visibles** mediante la API, el JSON presentable y una vista web mínima (`/dashboard`), además de los informes técnicos en disco cuando proceda.

En mi valoración, estos tres puntos definen si el proyecto cumple su promesa mínima frente al tribunal: no “una demo aislada”, sino un **sistema articulado** con trazabilidad documental en `docs/`.

---

## 3. Resultados por categoría MVP

La siguiente síntesis amplía la [tabla de evaluación del corpus MVP](../04_delivery/mvp-evaluation-table.md) con el razonamiento que suele interesar en la defensa oral.

### 3.1. Command injection

Se alcanza **detección** con reglas reconocibles de Bandit y Semgrep, **clasificación** mediante `mvp_category` y mapeo a CWE-78 y OWASP Injection, y **remediación asistida** en patrones acotados (`subprocess` con `shell=True`, `os.system`, etc.) con **verificación** por re-análisis. Los límites son explícitos: no todo vector de inyección queda cubierto; el contenido dinámico del comando puede seguir siendo peligroso aunque desaparezca el patrón detectado inicialmente.

### 3.2. Uso inseguro de `yaml.load`

Es uno de los casos más **didácticos** del corpus: sustitución conservadora por `safe_load` donde el patrón lo permite, con verificación automática. Refuerza la idea de remediación **explicable** frente a transformaciones opacas.

### 3.3. `verify=False` en peticiones HTTPS

La remediación propone **`verify=True`**, verificando que el hallazgo asociado desaparece. Puede coexistir en el mismo fichero con otros avisos (por ejemplo ausencia de `timeout`), lo cual es una oportunidad para explicar en la defensa que el análisis estático **no “limpia” el fichero entero de golpe**, sino el hallazgo objetivo del flujo de verificación.

### 3.4. Peticiones sin `timeout` (`requests`)

Se demuestra remediación con parámetro `timeout` en llamadas a `requests`, con verificación. Queda acotado a **`requests`** en el MVP; otras librerías (p. ej. `httpx`) quedaron fuera por decisión de alcance, no por imposibilidad técnica absoluta.

### 3.5. `debug=True` en Flask

Corrección a `debug=False` con verificación. El propio documento de evaluación advierte que **no** se cubren todos los modos de activar debug (p. ej. variables de entorno), lo cual honestidad metodológica frente al tribunal.

### 3.6. SQL injection

Aquí el “resultado” es **distinto**: **detección y clasificación** sólidas, **propuesta** textual o de política, pero **sin** autofix general en el MVP. Evaluar este apartado es comprobar que el sistema **no fuerza** un parche automático arriesgado y que el modo `proposal_only` se comporta como está documentado en [`docs/05_remediations/`](../05_remediations/).

---

## 4. Duplicados, informativos y presentación al usuario

Un resultado parcialmente “negativo” en el sentido de usabilidad —pero **documentado de forma positiva**— es la multiplicidad de filas por el mismo fichero o línea: Bandit y Semgrep, reglas distintas, o avisos informativos (p. ej. B404 frente a B602). El proyecto aborda esto con trazabilidad por herramienta, categorías dedicadas (p. ej. `subprocess_import_info`) y el parámetro **`hide_info`** en la vista presentable, según [`docs/04_delivery/scan-noise-and-duplicates.md`](../04_delivery/scan-noise-and-duplicates.md).

En la evaluación del MVP considero aceptable que la lista completa sea **verbosa** siempre que exista una vista **legible** para demostración y quede claro qué se oculta y por qué.

---

## 5. Formas de observar los resultados (entregables visibles)

Más allá del código, los “resultados” incluyen **cómo** el usuario o el tribunal pueden comprobarlos:

- **Endpoints de análisis y pipeline** que exponen hallazgos normalizados y clasificados, y rutas de verificación de autofix donde están implementadas.
- **JSON presentable**, diseñado para exposición sin volcar JSON crudo de herramienta por cada hallazgo (véase [`docs/03_experiments/presentable-scan-json.md`](../03_experiments/presentable-scan-json.md)).
- **Dashboard HTML** servido por la propia aplicación, como prueba de integración mínima “aplicación web” acorde al título del TFG.

Estos elementos cumplen el criterio de visibilidad citado en la sección 2.

---

## 6. Limitaciones de la evaluación

Conviene ser explícito sobre lo que **no** se está afirmando:

- El corpus es **finito y orientado a patrones**: no generaliza estadísticamente a “todo el ecosistema Python”.
- El análisis estático **no** equivale a pentesting ni a revisión manual experta.
- La verificación automática se apoya en **re-ejecutar** las mismas clases de reglas: garantiza coherencia interna del MVP, no seguridad absoluta del programa.

Estas limitaciones no restan valor al TFG si se presentan como **fronteras del diseño**; lo restaría pretender una cobertura o una garantía que el alcance nunca incluyó.

---

## 7. Relación con otros capítulos de la memoria

- La **evolución del desarrollo** ([capítulo 01](01_evolucion_del_desarrollo.md)) explica *cómo* se llegó a este estado.
- El **marco teórico** ([capítulo 03](03_marco_teorico_y_estado_del_arte.md)) explica *en qué marcos* se interpretan los hallazgos.
- Este capítulo concentra *qué* se puede afirmar que el MVP **logra** y *bajo qué condiciones*.
- Las **conclusiones y el trabajo futuro** ([capítulo 05](05_conclusiones_y_trabajo_futuro.md)) cierran objetivos, lecciones aprendidas y líneas abiertas.

---

## Referencias cruzadas

- Tabla de evaluación MVP: [`docs/04_delivery/mvp-evaluation-table.md`](../04_delivery/mvp-evaluation-table.md)
- Ruido y duplicados: [`docs/04_delivery/scan-noise-and-duplicates.md`](../04_delivery/scan-noise-and-duplicates.md)
- JSON presentable: [`docs/03_experiments/presentable-scan-json.md`](../03_experiments/presentable-scan-json.md)
- Alcance: [`docs/00_scope.md`](../00_scope.md)
- Conclusiones y trabajo futuro: [`docs/07_memoria/05_conclusiones_y_trabajo_futuro.md`](05_conclusiones_y_trabajo_futuro.md)

---

*Texto elaborado como borrador de memoria del TFG, alineado con el estado del repositorio en el momento de su redacción.*
