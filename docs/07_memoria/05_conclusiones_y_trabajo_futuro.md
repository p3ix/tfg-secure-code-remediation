# Conclusiones y trabajo futuro

Este capítulo cierra la línea argumental de la memoria redactada en paralelo al repositorio: resume lo **conseguido** frente a los objetivos, las **lecciones** que considero más relevantes y las **líneas de continuación** que un proyecto como este podría seguir sin confundirlas con el alcance ya cerrado del MVP.

---

## 1. Conclusiones respecto a los objetivos

El **objetivo general** planteado al inicio —una aplicación web para analizar proyectos Python, detectar problemas de seguridad relevantes, relacionarlos con marcos reconocidos, proponer correcciones cuando sea razonable y verificar el resultado, con supervisión humana— se ha cubierto en la medida prevista para un **MVP acotado**: el backend integra Bandit y Semgrep, normaliza y clasifica hallazgos, expone análisis y pipeline de verificación donde está implementado, y ofrece vistas útiles para demostración (JSON presentable y dashboard).

Los **objetivos específicos** (modelo normalizado, parsers, cargador unificado, mapeo CWE/OWASP/ASVS, remediadores y verificadores para las categorías acordadas, orquestación, documentación y trazabilidad vía issues) se corresponden con artefactos concretos del repositorio y con los capítulos de [marco teórico](03_marco_teorico_y_estado_del_arte.md), [resultados y evaluación](04_resultados_y_evaluacion_del_mvp.md) y [evolución del desarrollo](01_evolucion_del_desarrollo.md).

La conclusión principal que defiendo ante el tribunal es que **no hace falta prometer inteligencia artificial opaca** para aportar valor: un diseño claro, herramientas estándar, una capa de datos propia y un ciclo **detect → repair → verify** bien acotado ya permiten demostrar competencias de ciberseguridad aplicada e ingeniería del software.

---

## 2. Lecciones aprendidas

### 2.1. Sobre el análisis estático

Integrar dos herramientas aporta **riqueza** pero también **ruido**: duplicados, reglas que compiten y avisos informativos que no deben confundirse con vulnerabilidades “primarias”. Aprendí que la parte difícil no es ejecutar Bandit o Semgrep, sino **decidir** cómo presentar y clasificar el resultado para que sea útil y honesto ([`docs/04_delivery/scan-noise-and-duplicates.md`](../04_delivery/scan-noise-and-duplicates.md)).

### 2.2. Sobre la remediación automática

La tentación de automatizar grandes refactors choca con la **responsabilidad**: un parche mal aplicado puede romper lógica o dar falsa confianza. Por eso las remediaciones del MVP son **conservadoras**, con verificación por re-análisis, y casos como **SQL injection** se dejan en modo propuesta. Esta disciplina —frustrante a veces— es coherente con un TFG defendible.

### 2.3. Sobre el proceso de desarrollo

Documentar decisiones en `docs/`, enlazar trabajo con **issues** y mantener CI alineada con el entorno local ha sido tan importante como el código. Sin ese hábito, la memoria que estás leyendo no podría apoyarse en evidencias verificables.

---

## 3. Trabajo futuro

El repositorio ya materializa parte de la ampliación (análisis vía ZIP y Git, ritual de documentación por fases, roadmap de IA en ADR-002); el hilo narrativo está en el [capítulo 06](06_roadmap_fases_y_cadencia_memoria.md) y en [`docs/01_roadmap_and_documentation_ritual.md`](../01_roadmap_and_documentation_ritual.md). En esta etapa mantengo una separación explícita entre flujos de consola web (`/dashboard`) y flujos solo API (`/analysis/git-clone`, `/analysis/pipeline/mvp-autofix-verification`) para no mezclar alcance de UX con capacidad backend. **Las líneas siguientes** siguen siendo válidas como continuación plausible, ordenadas de forma aproximada por impacto y esfuerzo.

1. **Ampliar el corpus** con proyectos reales anonimizados o fragmentos más grandes, midiendo falsos positivos/negativos de forma sistemática (evaluación cuantitativa).
2. **Deduplicación y priorización** más fina entre hallazgos de Bandit y Semgrep, sin perder trazabilidad de la regla origen.
3. **Integración en CI/CD** (GitHub Actions u otro) como *gate* opcional o informativo, con políticas por severidad.
4. **Soporte para más librerías y patrones** (p. ej. `httpx`, otras formas de configurar Flask en producción).
5. **Autenticación y multiusuario** si el producto dejara de ser un trabajo académico aislado.
6. **Uso prudente de modelos de lenguaje** para explicar hallazgos o sugerir parches, siempre con **validación humana** y tests —en línea con la reflexión sobre supervisión en [REF-017] del catálogo [`docs/06_references/README.md`](../06_references/README.md).

Cualquier ampliación debería replantear alcance, riesgos y criterios de verificación con la misma honestidad que el MVP.

---

## 4. Reflexión final

Este TFG no pretende cerrar el problema de la seguridad en aplicaciones Python; pretende demostrar que es posible **articular** detección, clasificación, remediación asistida y verificación en un único flujo comprensible, trazable y alineado con estándares reconocidos. Si el lector del tribunal o del repositorio entiende tanto el **valor** como los **límites** de lo implementado, se habrá cumplido la intención de este trabajo.

---

## Referencias cruzadas

- Introducción y estructura: [`docs/07_memoria/02_introduccion_y_estructura_de_la_memoria.md`](02_introduccion_y_estructura_de_la_memoria.md)
- Marco teórico: [`docs/07_memoria/03_marco_teorico_y_estado_del_arte.md`](03_marco_teorico_y_estado_del_arte.md)
- Resultados y evaluación: [`docs/07_memoria/04_resultados_y_evaluacion_del_mvp.md`](04_resultados_y_evaluacion_del_mvp.md)
- Evolución del desarrollo: [`docs/07_memoria/01_evolucion_del_desarrollo.md`](01_evolucion_del_desarrollo.md)
- Alcance: [`docs/00_scope.md`](../00_scope.md)

---

*Texto elaborado como borrador de memoria del TFG, alineado con el estado del repositorio en el momento de su redacción.*
