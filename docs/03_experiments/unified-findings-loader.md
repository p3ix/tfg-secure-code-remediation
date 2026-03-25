# Servicio unificado de carga de hallazgos

## Objetivo

En este paso del TFG se implementa una capa de servicio para cargar hallazgos normalizados desde Bandit y Semgrep y devolverlos en una colección común.

## Motivación

Tras implementar parsers independientes para Bandit y Semgrep, el siguiente paso lógico era crear una capa común que evitara depender de cada parser por separado en las fases posteriores del sistema.

## Resultado

El servicio permite:
- cargar hallazgos desde Bandit;
- cargar hallazgos desde Semgrep;
- combinar ambos conjuntos de resultados;
- devolver una lista homogénea de `NormalizedFinding`.

## Alcance actual

En esta fase el servicio:
- no realiza deduplicación avanzada;
- no fusiona hallazgos equivalentes;
- no enriquece todavía los resultados con clasificación completa OWASP/ASVS.

Su objetivo es servir como base intermedia entre la ejecución de herramientas y las fases posteriores de clasificación, remediación y verificación.

## Valor dentro del TFG

Este componente refuerza la arquitectura propia del sistema, ya que permite tratar los hallazgos de distintas herramientas de manera uniforme antes de su procesamiento posterior.
