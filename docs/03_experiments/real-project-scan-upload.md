# Experimento: análisis de proyectos reales (ZIP y Git)

## Objetivo

Documentar la primera ampliación del TFG más allá del corpus `fixtures/mvp/`: análisis con Bandit y Semgrep sobre código aportado como **ZIP** o mediante **clonado HTTPS** controlado.

## Endpoints

- `POST /analysis/upload-zip` — subida multipart; extracción con comprobación anti path-traversal y límite de tamaño (`TFG_ZIP_MAX_BYTES`).
- `POST /analysis/git-clone` — JSON `{"url": "https://..."}`; `git clone --depth 1`; hosts permitidos vía `TFG_GIT_ALLOWED_HOSTS`; desactivación global con `TFG_ENABLE_GIT_CLONE=0`.

## Implementación

Código en [`app/services/project_scan_service.py`](../../app/services/project_scan_service.py); configuración en [`app/config.py`](../../app/config.py).

## Riesgos

- Repositorios grandes o dependencias no instaladas pueden inflar tiempos o resultados de Semgrep.
- El clonado solo debe usarse en **entornos de confianza**; revisar licencias y datos sensibles antes de analizar código de terceros.

## Referencias

- [`docs/00_scope.md`](../00_scope.md) — alcance ampliado.
- [`docs/01_roadmap_and_documentation_ritual.md`](../01_roadmap_and_documentation_ritual.md) — ritual de documentación.
