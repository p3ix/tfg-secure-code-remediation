# Hoja de ruta, fases del TFG y ritual de documentación

## 1. Objetivo

Este documento fija la **hoja de ruta por fases** (base limpia → análisis real → IA) y el **ritual obligatorio** de trabajo: issue antes de cambios sustantivos, evidencia en `docs/`, y actualización periódica de la memoria en `docs/07_memoria/`. Complementa [`docs/01_methodology_and_planning.md`](01_methodology_and_planning.md).

## 2. Fases del proyecto (orden lógico)

| Fase | Enfoque | Evidencia típica |
|------|---------|------------------|
| **1 — Base limpia** | README, dependencias, CI, alcance actualizado | PR + `docs/00_scope.md` |
| **2 — Análisis real** | ZIP, ruta relativa bajo `TFG_LOCAL_ANALYSIS_ROOT`, clonado Git con límites | `docs/03_experiments/`, endpoints documentados en OpenAPI |
| **3 — IA** | Explicación o remediación asistida con supervisión humana | ADR, `docs/05_remediations/` o `docs/02_decisions/`, variables de entorno documentadas |

Las fases no son exclusivas en el tiempo: puede haber iteración dentro de cada una.

## 3. Ritual por hito (cada feature o bloque relevante)

1. **Issue en GitHub** (plantilla alineada con [`.cursor/rules/tfg-issue-before-changes.mdc`](../.cursor/rules/tfg-issue-before-changes.mdc)): título, objetivo, checklist, criterio de cierre, evidencias.
2. **Implementación** acotada al cierre de la issue.
3. **Documentación** mínima en `docs/`:
   - experimentos o notas en `docs/03_experiments/` si hay resultados reproducibles;
   - decisión en `docs/02_decisions/` si cambia arquitectura o criterios;
   - actualización de `docs/06_references/README.md` si entra una fuente nueva obligatoria.
4. **PR** con descripción que enlace la issue (`Closes #N` cuando proceda).

## 4. Cadencia de la memoria (`docs/07_memoria/`)

Cada **2–4 hitos mayores** (p. ej. cierre de una fase parcial o entrega intermedia acordada con el director):

- ampliar el capítulo de [evolución del desarrollo](07_memoria/01_evolucion_del_desarrollo.md), o
- añadir un apartado en [conclusiones / trabajo futuro](07_memoria/05_conclusiones_y_trabajo_futuro.md), o
- crear un capítulo breve nuevo si el volumen lo justifica.

Ver también [Roadmap, fases y cadencia de memoria](07_memoria/06_roadmap_fases_y_cadencia_memoria.md).

## 5. Qué no forma parte de este ritual diario

- La **entrega final** del PDF al tribunal (plantilla del centro, bibliografía definitiva en formato normativo) se aborda **más adelante**, cuando el desarrollo estabilice.
