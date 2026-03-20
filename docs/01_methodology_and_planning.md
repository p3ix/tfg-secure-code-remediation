# Metodología de trabajo y planificación del TFG

## 1. Objetivo de este documento

En este documento dejo definida la forma en la que voy a organizar, planificar y seguir el desarrollo del TFG. El objetivo es que el proyecto no se limite a una implementación técnica aislada, sino que quede respaldado por una metodología de trabajo clara, trazable y reutilizable posteriormente en la memoria final.

Dado que el TFG no solo será evaluado por el resultado funcional, sino también por el proceso seguido, considero importante dejar documentado desde una fase temprana cómo se estructuran las tareas, cómo se registran las decisiones y cómo se conserva la evidencia del desarrollo realizado.

## 2. Enfoque general de trabajo

He decidido organizar el TFG mediante un enfoque iterativo por bloques de trabajo o sprints. No se trata de aplicar Scrum de forma estricta, sino de utilizar una estructura de iteraciones que permita:

- dividir el trabajo en fases coherentes;
- priorizar objetivos alcanzables;
- revisar el avance del proyecto de forma continua;
- mantener trazabilidad sobre tareas, decisiones y entregables.

Este enfoque resulta adecuado para el contexto del TFG, ya que permite combinar desarrollo técnico, documentación, validación y preparación de la defensa sin perder visibilidad del estado general del proyecto.

## 3. Herramientas de planificación y seguimiento

Para la gestión del proyecto estoy utilizando principalmente el ecosistema de GitHub, con los siguientes elementos:

### 3.1. Repositorio GitHub

El repositorio centraliza:

- el código fuente del proyecto,
- la documentación técnica,
- los archivos de configuración,
- las evidencias del desarrollo.

El repositorio actúa como fuente principal de verdad del TFG.

### 3.2. GitHub Projects

GitHub Projects se utiliza como tablero principal de planificación y seguimiento. En él organizo las tareas del proyecto, las distribuyo por sprints y les asigno atributos como estado, prioridad, módulo, estimación o release objetivo.

De esta manera, el Project no solo sirve para organizarme durante el desarrollo, sino también como evidencia visible de planificación y control del trabajo.

### 3.3. GitHub Issues

Las issues se utilizan para representar unidades de trabajo concretas. En este proyecto, una issue puede corresponder tanto a una tarea de desarrollo como a una tarea de documentación, arquitectura, evaluación o preparación de release.

Cada issue debe indicar, al menos:

- qué se pretende conseguir;
- qué entra y qué queda fuera de la tarea;
- qué tareas concretas hay que realizar;
- qué criterios de aceptación debe cumplir;
- qué evidencias dejará una vez terminada.

### 3.4. Pull Requests

Las pull requests se utilizarán para integrar cambios relevantes en la rama principal de trabajo. Su función no es únicamente técnica, sino también documental, ya que ayudan a dejar rastro de qué cambios se introdujeron, cuándo y con qué objetivo.

### 3.5. Commits

Los commits se emplearán para registrar cambios de forma incremental. Procuraré que sus mensajes sean claros y suficientemente descriptivos para facilitar la trazabilidad del proceso.

### 3.6. Releases

Las releases servirán para marcar hitos relevantes del TFG. No se usarán solo como una formalidad final, sino como referencia de evolución del proyecto a lo largo de sus principales fases.

## 4. Estructura general por sprints

He dividido el desarrollo del TFG en cuatro sprints principales:

### Sprint 1 — Base técnica y organización
En esta fase se sitúan:
- la preparación del repositorio y el entorno,
- la configuración inicial del backend,
- la integración básica de pruebas y CI,
- la organización del proyecto,
- la documentación del alcance, metodología y arquitectura inicial.

### Sprint 2 — Detección y clasificación
Este sprint estará centrado en:
- preparar fixtures o ejemplos vulnerables,
- integrar Bandit y Semgrep,
- normalizar hallazgos,
- clasificar resultados y relacionarlos con estándares.

### Sprint 3 — Remediación y verificación
En esta fase el foco estará en:
- definir qué casos son autofixables en el MVP,
- generar propuestas de remediación,
- verificar los cambios mediante reanálisis y pruebas,
- documentar limitaciones y casos problemáticos.

### Sprint 4 — Producto final, calidad y defensa
El último sprint se orientará a:
- consolidar el producto final,
- preparar releases,
- completar evaluación y validación,
- pulir documentación,
- preparar memoria, vídeo y defensa.

## 5. Criterio de estimación de tareas

Para facilitar la planificación he decidido utilizar una escala simple de tamaño relativo en GitHub Projects:

- **XS**: tarea muy pequeña, resoluble en menos de 2 horas;
- **S**: tarea pequeña, entre 2 y 4 horas;
- **M**: tarea media, entre 4 y 8 horas;
- **L**: tarea grande, que requiere más de 8 horas o varias sesiones.

No se trata de una estimación exacta al minuto, sino de una referencia práctica para comparar el tamaño de las tareas y mantener una carga razonable dentro de cada sprint.

## 6. Clasificación de alcance de tareas

Además de la estimación, he decidido distinguir tres tipos de alcance en las tareas del proyecto:

- **MVP**: tareas que forman parte del producto funcional mínimo que quiero implementar;
- **Academic**: tareas necesarias para justificar, documentar, evaluar o defender el TFG;
- **Future**: posibles ampliaciones que quedan fuera del alcance principal, pero que conviene dejar identificadas.

Esta distinción me ayuda a no sobredimensionar el proyecto y a separar claramente lo imprescindible de lo deseable.

## 7. Criterio de trazabilidad

Uno de los objetivos metodológicos del TFG es que el proceso quede trazable. Para ello seguiré, como norma general, esta relación:

- una necesidad o bloque de trabajo relevante se registra como **issue**;
- la issue se organiza dentro de **GitHub Projects**;
- el trabajo se desarrolla sobre el repositorio mediante cambios versionados;
- cuando el cambio lo requiera, se integra mediante **pull request**;
- la evidencia final queda reflejada en commits, documentos, PRs, estado del Project y releases.

Además, procuraré que las decisiones importantes queden reflejadas en la carpeta `docs/`, de modo que no dependan únicamente del historial técnico del repositorio.

## 8. Criterio adoptado para la documentación

La documentación se tratará como una parte central del proyecto, no como una tarea secundaria para el final. Mi intención es que la carpeta `docs/` vaya creciendo de manera ordenada a medida que avance el desarrollo.

En particular, quiero conservar evidencia de:

- alcance y decisiones de diseño;
- arquitectura inicial y cambios relevantes;
- experimentos realizados;
- fallos encontrados;
- remediaciones aplicadas;
- limitaciones observadas;
- referencias técnicas y normativas útiles para la memoria.

## 9. Situación inicial del proyecto

En la fase inicial del TFG ya he realizado varias tareas de base técnica, entre ellas:

- creación del repositorio;
- configuración del entorno con WSL y VS Code;
- puesta en marcha de FastAPI;
- creación de un endpoint `/health`;
- configuración de pytest;
- configuración de pre-commit;
- configuración básica de GitHub Actions;
- creación de ramas `main` y `develop`;
- creación inicial del Project y de documentación base.

Parte de este trabajo inicial no se registró desde el primer momento como issues individuales. A partir de este punto, el objetivo es trabajar con un nivel de trazabilidad más formal, registrando de forma más sistemática las tareas relevantes.

## 10. Plan inicial de releases

He definido una estructura mínima de releases para ordenar la evolución del proyecto:

- **v0.1**: base técnica y documentación inicial;
- **v0.2**: detección y clasificación funcional;
- **v0.3**: remediación y verificación inicial;
- **v1.0**: versión final del TFG, preparada para entrega y defensa.

Estas releases no deben entenderse como versiones comerciales del producto, sino como hitos del desarrollo que me ayudarán a ordenar el progreso y a justificar la evolución del trabajo.

## 11. Cierre de esta fase

Con este documento dejo cerrada la planificación inicial del TFG a nivel metodológico. A partir de esta base, el siguiente paso será centrar el trabajo en la implementación técnica del núcleo del proyecto, comenzando por la preparación de ejemplos vulnerables y la integración del análisis estático con Bandit y Semgrep.

El objetivo es avanzar sobre una base de trabajo ya ordenada, con alcance acotado, arquitectura definida y una metodología suficiente para mantener el proyecto controlado y defendible.
