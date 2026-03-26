# Segunda remediación asistida: verify=False

## Objetivo

Implementar una remediación asistida y conservadora para peticiones HTTPS con `verify=False`, y verificar posteriormente si el hallazgo objetivo desaparece al reanalizar el contenido corregido.

## Estrategia de remediación

En esta primera versión, la propuesta consiste en sustituir:

```python
verify=False
```
por:

```python
verify=True
```
en casos simples y explícitos con requests o httpx.

## Criterio de verificación

La verificación se considera satisfactoria si, tras aplicar la propuesta, no aparecen hallazgos clasificados como verify_false.

Es importante señalar que pueden seguir existiendo otros hallazgos no relacionados, por ejemplo missing_timeout. En ese caso, la verificación del objetivo concreto sigue considerándose correcta, aunque el archivo no quede completamente libre de problemas.

## Limitaciones

Esta primera versión no cubre:

- configuraciones TLS más complejas;
- lógica condicional alrededor del parámetro verify;
- patrones muy dinámicos o no explícitos.
