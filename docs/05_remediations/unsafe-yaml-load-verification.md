# Verificación inicial de remediación: yaml.load inseguro

## Objetivo

Comprobar si la remediación propuesta para `yaml.load` inseguro elimina el hallazgo al volver a ejecutar Bandit y Semgrep sobre el contenido corregido.

## Estrategia

La verificación se realiza de la siguiente forma:

1. se genera una propuesta de remediación sobre el contenido vulnerable;
2. se guarda el contenido corregido en un archivo temporal;
3. se ejecutan Bandit y Semgrep sobre ese archivo;
4. se parsean los resultados con el pipeline ya implementado;
5. se comprueba si siguen existiendo hallazgos clasificados como `unsafe_yaml_load`.

## Criterio de éxito

La verificación se considera satisfactoria si, tras la remediación, no aparecen hallazgos de la categoría `unsafe_yaml_load`.

## Alcance

Esta verificación está limitada a:
- un caso concreto del MVP;
- un patrón simple de remediación;
- una validación técnica basada en reanálisis estático.

No pretende garantizar corrección semántica completa ni sustituir validación humana.
