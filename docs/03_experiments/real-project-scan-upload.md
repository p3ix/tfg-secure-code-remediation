# Experimento: análisis de proyectos reales (ZIP y Git)

## Objetivo

Documentar la primera ampliación del TFG más allá del corpus `fixtures/mvp/`: análisis con Bandit y Semgrep sobre código aportado como **ZIP**, como **ruta relativa bajo una raíz de servidor** (`TFG_LOCAL_ANALYSIS_ROOT`) o mediante **clonado HTTPS** controlado.

## Endpoints

- `POST /analysis/upload-zip` — subida multipart; extracción con comprobación anti path-traversal y límite de tamaño (`TFG_ZIP_MAX_BYTES`).
- `POST /analysis/local-path` — JSON `{"relative_path": "..."}`; solo si `TFG_LOCAL_ANALYSIS_ROOT` apunta a un directorio en el servidor; rechaza rutas absolutas y componentes `..`.
- `POST /analysis/git-clone` — JSON `{"url": "https://..."}`; `git clone --depth 1`; hosts permitidos vía `TFG_GIT_ALLOWED_HOSTS`; desactivación global con `TFG_ENABLE_GIT_CLONE=0`.

## Implementación

Código en [`app/services/project_scan_service.py`](../../app/services/project_scan_service.py); configuración en [`app/config.py`](../../app/config.py). Los subprocesos Bandit y Semgrep comparten un límite de tiempo configurable (`TFG_ANALYSIS_TIMEOUT_SEC`, ver [`app/services/runtime_analysis_service.py`](../../app/services/runtime_analysis_service.py) y `run_analysis_command`).

## Exclusiones en proyectos grandes

- **Variable `TFG_ANALYSIS_EXCLUDE_DIRS`:** lista separada por comas (por defecto incluye `.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `dist`, `build`, caches, etc.). El backend traduce eso a la opción **`-x`** de Bandit y a varias banderas **`--exclude=...`** de Semgrep, para no recorrer directorios pesados o ajenos al código propio.
- **Fichero `.semgrepignore`:** Semgrep (oficialmente) puede leer un fichero llamado **`.semgrepignore`** en el directorio que se escanea, con sintaxis inspirada en `.gitignore`, para **omitir rutas** adicionales (tests generados, assets, etc.). Ese fichero pertenece al **proyecto analizado** (por ejemplo dentro de un repo clonado), no al TFG. Si existe, **se aplica en paralelo** a las exclusiones del backend: no sustituye la variable, las reglas se combinan.

## Riesgos

- Repositorios grandes o dependencias no instaladas pueden inflar tiempos o resultados de Semgrep.
- El clonado solo debe usarse en **entornos de confianza**; revisar licencias y datos sensibles antes de analizar código de terceros.

## Referencias

- [`docs/00_scope.md`](../00_scope.md) — alcance ampliado.
- [`docs/01_roadmap_and_documentation_ritual.md`](../01_roadmap_and_documentation_ritual.md) — ritual de documentación.
