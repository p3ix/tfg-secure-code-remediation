# Primera remediación asistida: yaml.load inseguro

## 1. Objetivo

En esta fase del TFG se implementa una primera remediación asistida para el caso de uso inseguro de `yaml.load`.

El objetivo no es construir todavía un sistema general de reescritura automática, sino demostrar que el flujo detect–repair–verify puede comenzar a materializarse de forma prudente sobre un caso concreto del MVP.

## 2. Criterio adoptado

Se ha elegido empezar por `yaml.load` inseguro porque:
- es un caso claro del MVP;
- tiene una alternativa segura reconocida (`yaml.safe_load`);
- y permite una remediación simple y verificable en ejemplos controlados.

## 3. Alcance de esta primera versión

La primera versión del remediador cubre únicamente patrones simples del tipo:

```python
yaml.load(data, Loader=yaml.Loader)
```

o equivalentes con loaders inseguros explícitos.

En estos casos, la propuesta consiste en sustituir la llamada por:
```python
yaml.safe_load(data)
```

## 4. Limitaciones

Esta primera versión no cubre:

- patrones multilinea complejos;
- usos dinámicos o altamente parametrizados;
- decisiones semánticas avanzadas sobre loaders personalizados;
- reescritura automática del proyecto completo.

Estas limitaciones son deliberadas, ya que el objetivo del MVP es priorizar casos conservadores y verificables.

## 5. Valor dentro del TFG

Esta remediación inicial es importante porque:

- marca el paso desde la detección hacia la reparación;
- demuestra una primera propuesta concreta de cambio;
- y deja preparada la fase siguiente de verificación posterior.
