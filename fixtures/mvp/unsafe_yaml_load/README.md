# Unsafe yaml.load

## Objetivo
Caso simple de deserialización YAML potencialmente insegura.

## Caso incluido
- uso de `yaml.load` con loader inseguro o no recomendado

## Expectativa
La muestra debería ser detectable y fácilmente remediable, por ejemplo sustituyendo por `yaml.safe_load` cuando el contexto lo permita.

## Papel en el MVP
Caso prioritario de remediación asistida.
