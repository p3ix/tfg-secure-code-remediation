# SQL injection

## Objetivo
Caso simple de construcción insegura de consulta SQL mediante interpolación de entrada.

## Caso incluido
- consulta SQL formada con f-string

## Expectativa
La muestra puede ser detectable mediante análisis estático, pero en el MVP no se considera adecuada para parche automático general.

## Papel en el MVP
Categoría de detección y propuesta, sin autofix automático.
