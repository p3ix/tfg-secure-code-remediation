# Ruido en el escaneo: duplicados y hallazgos informativos

## Duplicidad Bandit y Semgrep

Un mismo fichero y línea puede aparecer **dos veces** (o más) porque **Bandit** y **Semgrep** emiten reglas distintas sobre el mismo patrón. Esto no es un fallo del normalizador: el sistema prioriza **trazabilidad** (qué herramienta y qué regla disparó el aviso) frente a deduplicar automáticamente. En la memoria se puede argumentar que una evolución futura podría agrupar por `(fichero, línea, categoría MVP)`.

## Bandit B404 (import de `subprocess`)

La regla **B404** avisa de que se importa el módulo `subprocess`. En el corpus MVP de `command_injection` ese aviso es **contextual**: no es el mismo problema que `shell=True` (B602), pero ayuda a entender el archivo. El parser usa la categoría propia **`subprocess_import_info`** cuando la ruta está bajo `command_injection/`, con:

- `remediation_mode`: `detection_only` (sin autofix para ese aviso),
- mismo marco CWE/OWASP que inyección de comandos en el mapper, por contexto educativo,
- título descriptivo en lugar de “Hallazgo de seguridad” genérico.

Así desaparece `unknown` y el verificador de remediación autofix sigue comprobando solo `command_injection` (B602/B605, etc.), sin contar B404 tras el parche.

## Parámetro `hide_info` (vista demo)

Los endpoints presentables y el `/dashboard` admiten **`hide_info=true`**: ocultan hallazgos con remediación solo detección o severidad baja, y recalculan el resumen. Sirve para demos y capturas de pantalla; el listado completo es el comportamiento por defecto (`hide_info=false`).
