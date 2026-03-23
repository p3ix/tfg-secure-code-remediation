# HTTPS verify=False

## Objetivo
Caso simple de desactivación de verificación TLS en peticiones HTTPS.

## Caso incluido
- `requests.get(..., verify=False)`

## Expectativa
La muestra debería ser detectable mediante análisis estático y candidata a propuesta de remediación.

## Papel en el MVP
Caso prioritario de remediación asistida.
