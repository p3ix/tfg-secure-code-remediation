# Corpus inicial de fixtures vulnerables del MVP

Este directorio contiene un conjunto inicial de ejemplos vulnerables controlados para el MVP del TFG.

## Objetivo
Servir como base experimental para:
- probar la detección con Bandit y Semgrep,
- evaluar el alcance real del MVP,
- preparar la fase posterior de remediación y verificación.

## Criterios de diseño
- ejemplos pequeños y acotados,
- una vulnerabilidad principal por archivo,
- trazabilidad clara,
- facilidad de análisis automático.

## Categorías incluidas
- command injection
- unsafe yaml.load
- verify=False
- missing timeout
- Flask debug=True
- SQL injection (solo detección/propuesta en MVP)
