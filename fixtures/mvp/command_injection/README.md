# Command injection

## Objetivo
Casos simples de ejecución insegura de comandos del sistema.

## Casos incluidos
- uso de `subprocess.run(..., shell=True)`
- uso de `os.system(...)`

## Expectativa
Estas muestras deberían ser detectables por herramientas de análisis estático orientadas a seguridad en Python.

## Papel en el MVP
Categoría candidata a remediación asistida en casos acotados y verificables.
