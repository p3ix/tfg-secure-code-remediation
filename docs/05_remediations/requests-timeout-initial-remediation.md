# Cuarta remediación asistida: requests sin timeout

## Objetivo

Implementar una remediación asistida y conservadora para llamadas `requests` sin `timeout`, y verificar posteriormente si el hallazgo objetivo desaparece al reanalizar el contenido corregido.

## Estrategia de remediación

En esta primera versión, la propuesta consiste en añadir:

```python
timeout=10
```

a llamadas simples de requests donde no exista un timeout explícito.

## Justificación

La documentación oficial de Requests recomienda usar timeout en casi todo código de producción y advierte de que, si no se especifica, las peticiones pueden quedarse esperando indefinidamente. Por este motivo, el caso de requests sin timeout se considera adecuado para una remediación conservadora dentro del MVP.

## Alcance y límites

Esta primera versión:

- cubre únicamente llamadas simples de requests sin timeout;
- no cubre todavía patrones complejos;
- no cubre httpx en esta iteración.

La razón para no incluir httpx en esta primera remediación es que la documentación oficial de HTTPX indica que aplica timeouts por defecto, por lo que su tratamiento requiere una revisión más cuidadosa y no conviene forzarlo dentro del MVP inicial.
