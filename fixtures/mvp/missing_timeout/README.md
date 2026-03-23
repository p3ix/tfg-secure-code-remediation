# Missing timeout

## Objetivo
Casos simples de peticiones HTTP realizadas sin timeout explícito.

## Casos incluidos
- `requests.get(...)` sin `timeout`
- `httpx.get(...)` sin `timeout`

## Expectativa
Estas muestras pueden requerir reglas específicas para una detección consistente, especialmente en Semgrep.

## Papel en el MVP
Caso prioritario de propuesta de remediación y verificación posterior.
