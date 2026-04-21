# Evolución del desarrollo, decisiones y dificultades

Este capítulo describe, desde la perspectiva del desarrollo del proyecto, cómo se ha ido construyendo el trabajo, qué decisiones se han tomado en cada fase y qué dificultades han aparecido. La numeración de las tareas se relaciona con las *issues* del repositorio en GitHub, donde queda trazabilidad adicional. El **contexto, los objetivos y la estructura prevista de la memoria** están en el capítulo de [introducción y estructura de la memoria](02_introduccion_y_estructura_de_la_memoria.md).

El orden que sigo no es estrictamente cronológico en cada párrafo, sino **lógico**: primero organización y base, después detección y modelo de datos, después remediación y verificación, y por último la capa de presentación y los ajustes de usabilidad del resultado del escaneo.

---

## 1. Organización del trabajo y base del proyecto

Al inicio del TFG fue necesario **definir un backlog detallado** y **documentar una arquitectura inicial** acorde al alcance acotado que ya había fijado en el documento de alcance: aplicación web orientada a Python, flujo detect–repair–verify y supervisión humana, sin pretender una plataforma multilenguaje ni un sistema autónomo que corrija código sin control.

En paralelo se **preparó la estructura del proyecto**: repositorio en GitHub, ramas de trabajo, entorno local con WSL y Visual Studio Code, y la configuración básica de calidad (por ejemplo `pre-commit` y CI con GitHub Actions). Esta base no es el núcleo científico del TFG, pero condiciona todo lo demás: sin un flujo de trabajo ordenado y repetible, es difícil defender un proceso de desarrollo trazable ante el tribunal.

También se **definió la planificación por sprints y releases** y, a nivel de documentación interna, una **planificación inicial** que enlaza con la metodología descrita en `docs/01_methodology_and_planning.md`. La decisión consciente aquí fue **priorizar viabilidad**: un estudiante de Grado no puede mantener el mismo ritmo que un equipo industrial; por eso los sprints se usaron como marco de referencia, no como presión artificial de entregar funcionalidades incompletas.

---

## 2. Corpus de fixtures y primeras integraciones de análisis estático

Una decisión temprana y central fue **crear un corpus inicial de fixtures vulnerables** propio del MVP. En lugar de depender solo de ejemplos dispersos de internet, se preparó un conjunto de ficheros Python bajo `fixtures/mvp/`, cada uno ilustrando un patrón concreto (por ejemplo `yaml.load` inseguro, `verify=False`, ausencia de `timeout` en `requests`, `debug=True` en Flask, patrones de inyección de comandos, y un caso de SQL injection con alcance limitado a detección y propuesta).

Sobre ese corpus se integró **Bandit** y se documentó la **primera ejecución de análisis**; después se integró **Semgrep** y se comparó la cobertura respecto a Bandit. La decisión de usar **dos herramientas** no responde a un capricho técnico, sino a una necesidad académica defendible: Bandit está muy orientado a patrones típicos de Python inseguro, mientras que Semgrep aporta reglas más transversales y, en la práctica, **solapamiento y complemento** entre ambas. Ese solapamiento no es un error del proyecto: es un hecho que más adelante obligó a reflexionar sobre cómo presentar resultados sin duplicar confusión al usuario (véase la sección 6).

---

## 3. Modelo normalizado, parsers y carga unificada

Para no acoplar el backend al formato nativo de cada herramienta, se **diseñó un modelo normalizado de hallazgos** (`NormalizedFinding`, documentado en `docs/01_normalized_findings_model.md`). La decisión principal fue introducir una **capa intermedia propia**: los informes JSON de Bandit y Semgrep se transforman en una estructura común que luego puede clasificarse, mostrarse y, en algunos casos, remediarse.

Sobre ese diseño se implementaron el **parser de Bandit** y el **parser de Semgrep** hacia el modelo normalizado, y a continuación un **servicio unificado de carga** que combina ambas fuentes y ordena los resultados de forma determinista. Aquí la dificultad no fue solo técnica (mapear campos distintos), sino de **criterio**: cada hallazgo debía recibir una **categoría MVP** coherente con el alcance (`mvp_category`) y un **modo de remediación** (`remediation_mode`) que distingue entre candidatos a autofix, propuesta sin parche automático (como SQL injection) y meramente informativos.

---

## 4. Clasificación, API de análisis y ejecución en tiempo de ejecución

Una vez normalizados los hallazgos, se añadió una capa de **mapeo a estándares** (CWE, OWASP Top 10, OWASP ASVS cuando procede), descrita en `docs/01_findings_classification_mapping.md`. La decisión fue mantener el mapeo **determinista y basado en categoría MVP**, en lugar de intentar una inferencia semántica profunda que habría disparado el alcance.

A nivel de producto, se implementó un **endpoint de análisis sobre informes ya generados** (fixtures con reports en disco) y, más adelante, la **ejecución de Bandit y Semgrep desde el backend** sobre el directorio de fixtures, generando informes de ejecución en `reports/runtime/`. Esta segunda vía fue importante para demostrar que el sistema no depende solo de JSON precocinados, aunque añade complejidad operativa (tiempos de ejecución, dependencias de las herramientas en el entorno de despliegue y CI).

---

## 5. Remediación asistida y verificación: cierre del ciclo detect–repair–verify

El núcleo defendible del TFG es demostrar el ciclo **detect → repair → verify** con casos concretos del MVP, sin prometer una IA que “arregla todo”. Por ello se implementó una cadena de **remediadores conservadores** y **verificadores** que, sobre copias temporales del código, aplican una propuesta, relanzan el análisis estático y comprueban que el hallazgo objetivo desaparece o se reduce según el criterio definido.

El orden de trabajo en el repositorio siguió una progresión didáctica:

1. Primera remediación y verificación para **`yaml.load` inseguro**, por ser un caso claro y bien acotado.
2. Remediación y verificación para **`verify=False`** en peticiones HTTPS.
3. Remediación y verificación para **`debug=True`** en Flask.
4. Remediación y verificación para **peticiones `requests` sin `timeout`**, con la decisión explícita de **no tratar `httpx` igual en el MVP inicial**, por coherencia con la documentación de cada librería y para no inflar el alcance.
5. Remediación y verificación para **command injection** en patrones reconocibles (`shell=True`, `os.system`), documentando limitaciones fuertes.

Para **SQL injection** se tomó la decisión acorde al alcance: **solo detección y propuesta**, sin parche automático general en el MVP, dado el riesgo de romper lógica de negocio. Esto está reflejado en el modo `proposal_only` y en la documentación específica bajo `docs/05_remediations/`.

La principal **dificultad conceptual** en esta fase fue resistir la tentación de automatizar demasiado: cada remediador debía ser **explicable**, **reproducible** y **verificable** con tests, no una caja negra.

---

## 6. Orquestación, salida presentable, dashboard y ruido en el escaneo

Cuando el conjunto de piezas ya funcionaba, faltaba **integrar el flujo** de forma inteligible: se implementó un **orquestador del pipeline** que resume el análisis clasificado y permite lanzar una ronda de verificación autofix sobre fixtures canónicos del MVP, sin mezclar responsabilidades con la API cruda de depuración.

En paralelo se definió un **JSON de salida presentable** (sin volcados crudos de herramienta por hallazgo) y, para acercar el trabajo al título de “aplicación web”, un **dashboard HTML** servido por el propio FastAPI, alimentado con la misma lógica que el JSON presentable.

Aquí aparecieron dos fenómenos que ya se habían entrever en las *issues* del proyecto:

1. **Solapamiento entre Bandit y Semgrep** sobre el mismo fichero o línea, lo que genera varias filas “duplicadas” desde el punto de vista del usuario. La decisión fue **priorizar trazabilidad** (saber qué regla de qué herramienta disparó el aviso) frente a deduplicar agresivamente en una primera versión.

2. **Hallazgos secundarios o informativos**, en particular el **B404** de Bandit (importación de `subprocess`), que no deberían tratarse igual que una vulnerabilidad principal como `shell=True`. Tras iterar, se introdujo una **categoría específica** (`subprocess_import_info`) con modo de remediación acorde, y un **filtro opcional** `hide_info` en la vista presentable para demos y capturas de pantalla, documentado en `docs/04_delivery/scan-noise-and-duplicates.md`.

Esta parte del trabajo ilustra bien una tensión habitual en ingeniería: los datos “crudos” son fieles pero ruidosos; la vista “limpia” es cómoda pero puede ocultar matices. Por eso quedó **documentado el criterio del filtro** y se mantiene siempre accesible el listado completo por defecto.

---

## 7. Dificultades transversales

Más allá de los detalles por *issue*, conviene resumir dificultades que se repitieron:

- **Gestión del repositorio y artefactos generados**: los informes en `reports/`, especialmente los de ejecución *runtime*, pueden cambiar por efecto de los hooks de formato o de volver a ejecutar análisis. Esto enseña a separar mentalmente **código versionado** de **artefactos regenerables**, y a ser cuidadoso al hacer `commit` para no mezclar cambios funcionales con mero reformateo de JSON.

- **Entorno de CI vs entorno local**: las pruebas que invocan Bandit y Semgrep requieren que esas herramientas estén instaladas y, en algunos casos, acceso a red para reglas de Semgrep. Mantener alineada la instalación en CI y en local fue parte del trabajo invisible pero necesario.

- **Equilibrio entre alcance y tiempo de TFG**: varias funcionalidades tentadoras (multilenguaje, integración profunda con GitHub, IA generativa que reescribe proyectos enteros) se **descartaron de forma explícita** para preservar un MVP defendible.

---

## 8. Estado del trabajo y relación con la memoria final

Al cierre de la etapa descrita en este documento, el repositorio incluye: corpus MVP, integración de Bandit y Semgrep, modelo normalizado, clasificación por estándares, endpoints de análisis, remediación y verificación para los casos autofix del alcance, orquestador, JSON presentable, dashboard, documentación de remediaciones y de entrega, y reglas de proyecto (por ejemplo emisión de *issues* antes de cambios sustantivos, reflejada en `.cursor/rules/`).

Lo que queda para la **memoria escrita** no es repetir el código línea a línea, sino **tejer narrativa**: motivación, marco teórico (OWASP, CWE, ASVS, NIST SSDF donde aplique), metodología, resultados y limitaciones. La **introducción y el mapa de capítulos** están esbozados en [02_introduccion_y_estructura_de_la_memoria.md](02_introduccion_y_estructura_de_la_memoria.md); el **marco teórico y estado del arte** se desarrolla en [03_marco_teorico_y_estado_del_arte.md](03_marco_teorico_y_estado_del_arte.md). Este capítulo sirve como **puente** entre el trabajo real en GitHub y esa narrativa: aquí se cuenta *qué se hizo y por qué*; en los capítulos formales de la memoria se profundizará en *cómo se fundamenta* frente al estado del arte y al tribunal.

---

## 9. De fixtures sintéticos a proyectos reales

Tras consolidar el MVP sobre `fixtures/mvp/`, el siguiente paso defendible fue **salir del corpus controlado** sin abrir el servidor a rutas arbitrarias. Se implementaron tres vías complementarias: subida de un **ZIP** con extracción acotada y comprobación anti path-traversal; análisis bajo una **raíz local** configurable (`TFG_LOCAL_ANALYSIS_ROOT`) aceptando solo rutas relativas validadas; y **clonado Git** HTTPS con lista de hosts permitidos y timeout de clonado. En todos los casos se reutiliza el mismo pipeline **Bandit + Semgrep** que ya había validado los fixtures, y se añadieron **límites de tiempo por subproceso** para reducir el riesgo de que un árbol de ficheros enorme bloquee indefinidamente el backend. Para proyectos voluminosos se configuró además una lista de **exclusiones** (`TFG_ANALYSIS_EXCLUDE_DIRS`) que alimenta Bandit y Semgrep, reconociendo que Semgrep puede respetar también un **`.semgrepignore`** en el propio proyecto analizado. Esta ampliación no reemplaza la evaluación sobre el corpus MVP, pero sí prepara el relato del TFG para incorporar **código o repositorios reales** en iteraciones posteriores, con los avisos de licencia, privacidad y datos sensibles ya recogidos en el documento de alcance.

---

## Referencias cruzadas en el repositorio

Para no duplicar contenido técnico, este capítulo se apoya en documentos ya existentes, entre otros:

- Introducción y estructura de la memoria: [`docs/07_memoria/02_introduccion_y_estructura_de_la_memoria.md`](02_introduccion_y_estructura_de_la_memoria.md)
- Marco teórico y estado del arte: [`docs/07_memoria/03_marco_teorico_y_estado_del_arte.md`](03_marco_teorico_y_estado_del_arte.md)
- Resultados y evaluación del MVP: [`docs/07_memoria/04_resultados_y_evaluacion_del_mvp.md`](04_resultados_y_evaluacion_del_mvp.md)
- Conclusiones y trabajo futuro: [`docs/07_memoria/05_conclusiones_y_trabajo_futuro.md`](05_conclusiones_y_trabajo_futuro.md)
- Roadmap y cadencia de memoria: [`docs/07_memoria/06_roadmap_fases_y_cadencia_memoria.md`](06_roadmap_fases_y_cadencia_memoria.md)
- Hoja de ruta y ritual de documentación: [`docs/01_roadmap_and_documentation_ritual.md`](../01_roadmap_and_documentation_ritual.md)
- Alcance: [`docs/00_scope.md`](../00_scope.md)
- Arquitectura: [`docs/01_architecture_overview.md`](../01_architecture_overview.md)
- Modelo normalizado: [`docs/01_normalized_findings_model.md`](../01_normalized_findings_model.md)
- Clasificación: [`docs/01_findings_classification_mapping.md`](../01_findings_classification_mapping.md)
- Tabla de evaluación MVP: [`docs/04_delivery/mvp-evaluation-table.md`](../04_delivery/mvp-evaluation-table.md)
- Ruido y duplicados: [`docs/04_delivery/scan-noise-and-duplicates.md`](../04_delivery/scan-noise-and-duplicates.md)
- Remediaciones: carpeta [`docs/05_remediations/`](../05_remediations/)

---

*Texto elaborado como borrador de memoria del TFG, alineado con el estado del repositorio en el momento de su redacción.*
