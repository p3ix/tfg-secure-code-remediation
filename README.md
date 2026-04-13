# TFG Secure Code Remediation

Aplicación web para análisis y remediación asistida por IA de vulnerabilidades en proyectos Python.

## Estado del proyecto

El **MVP** sobre `fixtures/mvp/` está operativo: detección con Bandit y Semgrep, modelo normalizado de hallazgos, clasificación CWE/OWASP/ASVS, remediación asistida con verificación en patrones acotados, pipeline, dashboard y JSON presentable (incl. agrupación opcional `group_equivalent`).

En **ampliación**: análisis de **proyectos reales** (subida ZIP, ruta local bajo directorio permitido, clonado Git HTTPS acotado), capa **IA** opcional documentada en [`docs/02_decisions/ADR-002-ai-assisted-roadmap.md`](docs/02_decisions/ADR-002-ai-assisted-roadmap.md).

## Documentación clave

| Documento | Contenido |
|-----------|-----------|
| [`docs/00_scope.md`](docs/00_scope.md) | Alcance MVP y fases siguientes |
| [`docs/01_roadmap_and_documentation_ritual.md`](docs/01_roadmap_and_documentation_ritual.md) | Hoja de ruta, ritual issues/docs, cadencia memoria |
| [`docs/01_architecture_overview.md`](docs/01_architecture_overview.md) | Arquitectura |
| [`docs/06_references/README.md`](docs/06_references/README.md) | Referencias [REF-xxx] |

## Stack

- Python 3.12+
- FastAPI, Uvicorn, Jinja2
- Bandit, Semgrep
- pytest, httpx (tests)
- pre-commit (opcional local)
- GitHub Actions (CI)

## Entorno de desarrollo

Se recomienda un **venv** e instalar dependencias del proyecto y herramientas de análisis en el `PATH`:

```bash
cd /path/to/TFG
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e ".[dev]"
export PATH="$PWD/.venv/bin:$PATH"
```

`bandit` y `semgrep` deben ser invocables por el backend (subprocesos). Semgrep puede necesitar **red** la primera vez para reglas.

## Ejecutar la API

```bash
uvicorn app.main:app --reload
```

- Salud: `GET http://127.0.0.1:8000/health`
- Dashboard: `GET http://127.0.0.1:8000/dashboard`
- OpenAPI: `http://127.0.0.1:8000/docs`

### Análisis de proyectos reales (nuevo)

- `POST /analysis/upload-zip` — cuerpo: fichero `multipart/form-data` (campo típico `file`). Límite por defecto ~20 MB (`TFG_ZIP_MAX_BYTES`).
- `POST /analysis/local-path` — JSON `{"relative_path": "mi-proyecto"}`: analiza un subdirectorio **relativo** bajo `TFG_LOCAL_ANALYSIS_ROOT` (definir en el servidor; sin rutas absolutas ni `..`). Si la variable no está definida, el endpoint responde 403.
- `POST /analysis/git-clone` — JSON `{"url": "https://github.com/org/repo"}` (HTTPS, hosts permitidos por `TFG_GIT_ALLOWED_HOSTS`). Desactivar clonado con `TFG_ENABLE_GIT_CLONE=0`.

### Estado de la capa IA (roadmap)

- `GET /ai/status` — indica si las explicaciones IA están habilitadas (`TFG_AI_EXPLANATIONS_ENABLED`) y si hay raíz local configurada para `/analysis/local-path`.

## Tests

```bash
export PATH="$PWD/.venv/bin:$PATH"
pytest -q
```

En CI (Ubuntu) las dependencias se instalan como en [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Licencia

Ver el fichero `LICENSE` del repositorio si existe.
