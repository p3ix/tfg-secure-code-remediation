# Roadmap por fases y cadencia de la memoria

Este capítulo enlaza la **hoja de ruta técnica** del TFG con la forma en que voy **actualizando la memoria** durante el curso, sin esperar al cierre final.

---

## 1. Fases de trabajo (visión actual)

Los detalles operativos están en [`docs/01_roadmap_and_documentation_ritual.md`](../01_roadmap_and_documentation_ritual.md). En resumen:

| Fase | Contenido |
|------|-----------|
| **1 — Base limpia** | Repositorio legible, README, CI, alcance coherente con el código. |
| **2 — Análisis real** | Proyectos reales: subida ZIP, ruta relativa bajo `TFG_LOCAL_ANALYSIS_ROOT`, clonado Git acotado; mismos analizadores que el MVP sobre fixtures. |
| **3 — IA** | Capa opcional de explicación o sugerencias, con supervisión humana y variables de entorno documentadas (ADR-002). |

Estas fases **no sustituyen** los capítulos ya redactados sobre el MVP (evolución, introducción, marco teórico, resultados, conclusiones), sino que **amplían** el relato conforme avance el repositorio.

---

## 2. Cadencia de la memoria

Cada **2–4 hitos mayores** (por ejemplo: “análisis ZIP mergeado”, “primer prototipo de explicación IA”):

- actualizo el capítulo de [evolución del desarrollo](01_evolucion_del_desarrollo.md) con decisiones y dificultades nuevas, o
- amplío [conclusiones y trabajo futuro](05_conclusiones_y_trabajo_futuro.md) con líneas inmediatas ya contrastadas, o
- añado un subapartado en [resultados y evaluación](04_resultados_y_evaluacion_del_mvp.md) si hay métricas o tablas nuevas.

Así la memoria en `docs/07_memoria/` **acompaña** el código en lugar de quedarse congelada en el primer borrador.

---

## 3. Relación con issues y documentación

Cada hito sustantivo debe tener **issue** y **documentación** en `docs/` (experimentos, ADR, entrega), según la regla del repositorio. Este capítulo no redefine esa regla; solo fija la **cadencia** de volcar parte de ese material en prosa de memoria.

---

*Texto elaborado como borrador de memoria del TFG.*
