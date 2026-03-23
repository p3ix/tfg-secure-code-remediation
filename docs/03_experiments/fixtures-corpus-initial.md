# Corpus inicial de fixtures vulnerables

## Objetivo
Definir un conjunto inicial de ejemplos vulnerables pequeños y controlados para probar las capacidades de detección del MVP.

## Decisiones adoptadas
- cada categoría del MVP dispone de al menos un caso inicial;
- se priorizan ejemplos pequeños, legibles y analizables;
- SQL injection se incorpora solo como caso de detección/propuesta;
- no se incluyen todavía variantes corregidas para todos los casos.

## Utilidad dentro del TFG
Este corpus será la base para:
- la integración de Bandit;
- la integración de Semgrep;
- la comparación de cobertura entre herramientas;
- la fase posterior de remediación y verificación.

## Limitaciones
- el corpus inicial no es exhaustivo;
- no cubre proyectos completos;
- no representa toda la complejidad real del software en producción;
- está pensado como base del MVP y no como benchmark generalista.
