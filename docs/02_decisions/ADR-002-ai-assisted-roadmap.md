# ADR-002 — IA asistida: alcance y extensión futura

## Estado

Propuesta / en diseño (fase inicial del TFG).

## Contexto

El título del TFG menciona remediación **asistida por IA**. El MVP actual combina reglas SAST deterministas, remediaciones conservadoras y verificación por re-análisis, sin modelo generativo obligatorio.

## Decisión

1. **Separar** claramente:
   - **IA opcional** para *explicación* de hallazgos (texto educativo, citando CWE/OWASP) o *sugerencias* de parche, siempre **revisables** por el usuario.
   - **Pipeline actual** sin dependencia de API externa para el núcleo detect → classify → verify.

2. **Supervisión humana** y buenas prácticas alineadas con NIST SP 800-218A (véase [REF-017](../06_references/README.md)): no aplicar cambios ciegos; registrar qué modelo y qué prompt si se usa generación.

3. **Activación por entorno**: `TFG_AI_EXPLANATIONS_ENABLED=1` cuando exista integración; por defecto desactivado.

4. **Punto de extensión en API**: `GET /ai/status` documenta si la capa IA está habilitada y enlaza a este ADR.

## Consecuencias

- El backend puede evolucionar sin romper tests del núcleo.
- La memoria puede describir el roadmap de IA sin confundirlo con lo ya verificado en el MVP.

## Referencias

- [NIST SP 800-218A](https://csrc.nist.gov/pubs/sp/800/218/a/final) — prácticas con modelos generativos y doble uso.
- [`docs/00_scope.md`](../00_scope.md) — supervisión humana y límites del MVP.
