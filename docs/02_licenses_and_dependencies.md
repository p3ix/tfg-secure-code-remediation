# Licencias del proyecto y dependencias principales

## 1. Objetivo

En este documento recojo la licencia elegida para el repositorio del TFG y una revisión inicial de las licencias de las principales herramientas y dependencias utilizadas en el proyecto.

El objetivo es dejar constancia de que se ha tenido en cuenta la dimensión legal y de reutilización del software empleado, así como justificar la licencia elegida para el código desarrollado en el TFG.

## 2. Licencia del repositorio

He decidido publicar el repositorio del TFG bajo licencia **MIT**.

La elección de MIT se debe a que es una licencia permisiva, sencilla de entender y ampliamente utilizada en el ecosistema Python. Además, resulta adecuada para un proyecto académico en el que interesa facilitar la reutilización del código, manteniendo al mismo tiempo una atribución mínima y una renuncia estándar de responsabilidad.

## 3. Dependencias y herramientas revisadas

| Componente | Uso en el TFG | Licencia identificada | Observaciones |
|---|---|---|---|
| FastAPI | Backend de la aplicación | MIT | Compatible con el enfoque abierto y permisivo del proyecto |
| pytest | Pruebas | MIT | Uso habitual en proyectos Python |
| pre-commit | Calidad local y hooks | MIT | Herramienta de soporte al desarrollo |
| Bandit | Análisis estático de seguridad en Python | Apache-2.0 | Herramienta principal de detección en el MVP |
| Semgrep Community Edition | Análisis estático complementario | LGPL-2.1 (motor) | Se revisará cuidadosamente la licencia de las reglas utilizadas |
| Semgrep-maintained rules | Reglas de análisis mantenidas por Semgrep | Semgrep Rules License v1.0 | No se asumirán como reglas libremente redistribuibles sin revisar su licencia concreta |

## 4. Consideración específica sobre Semgrep

Semgrep requiere una atención especial dentro del apartado de licencias.

Por un lado, el motor de Semgrep Community Edition se distribuye bajo licencia **LGPL 2.1**. Por otro lado, las reglas mantenidas por Semgrep no comparten necesariamente esa misma licencia, ya que Semgrep indica que dichas reglas están gobernadas por la **Semgrep Rules License v1.0**.

Por este motivo, para evitar ambigüedades en el TFG se seguirá un criterio prudente:
- usar Semgrep CE como herramienta de análisis;
- priorizar reglas propias o reglas con licencia abierta claramente identificada;
- evitar incorporar al repositorio reglas mantenidas por terceros sin revisar antes sus condiciones de licencia.

## 5. Alcance de esta revisión

Esta revisión es inicial y se centra en las herramientas principales del proyecto. Si durante el desarrollo se añaden nuevas dependencias relevantes, se actualizará este documento para mantener la trazabilidad del análisis legal básico del stack.

## 6. Conclusión

La licencia elegida para el repositorio es **MIT**, mientras que las principales dependencias del stack usan licencias permisivas o ampliamente utilizadas en software libre. La única cautela especial en esta fase corresponde a Semgrep y al licenciamiento de sus reglas, por lo que se documenta expresamente esta limitación y se adopta una política conservadora de uso.
