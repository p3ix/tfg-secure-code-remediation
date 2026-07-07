# TFG Secure Code Remediation

[![CI](https://github.com/p3ix/tfg-secure-code-remediation/actions/workflows/ci.yml/badge.svg)](https://github.com/p3ix/tfg-secure-code-remediation/actions/workflows/ci.yml)

Aplicación web para el análisis de seguridad de proyectos Python: detección con **Bandit** y **Semgrep**, normalización y clasificación de hallazgos (CWE / OWASP Top 10 / OWASP ASVS), remediación asistida con verificación por reanálisis en patrones acotados, y una capa **opcional** de explicaciones asistidas por IA con proveedor local.

Trabajo de Fin de Grado de Asier Lara. La memoria y los anexos (manuales de usuario y de programador incluidos) se entregan por separado; este repositorio contiene el producto software. La trazabilidad del desarrollo puede consultarse en las [issues](https://github.com/p3ix/tfg-secure-code-remediation/issues?q=is%3Aissue), las [pull requests](https://github.com/p3ix/tfg-secure-code-remediation/pulls?q=is%3Apr) y el [`CHANGELOG.md`](CHANGELOG.md).

## Estado del proyecto

Versión **v1.0.0** ([releases](https://github.com/p3ix/tfg-secure-code-remediation/releases)), versión final del TFG. Todo el flujo está operativo:

- **Detección y clasificación**: Bandit + Semgrep sobre el corpus `fixtures/mvp/` o sobre proyectos reales, con modelo normalizado de hallazgos y referencias CWE/OWASP/ASVS.
- **Análisis de proyectos reales** desde web y API: subida **ZIP**, **clonado Git HTTPS** acotado y **ruta local** bajo una raíz permitida, con límites operativos configurables.
- **Remediación asistida y verificación**: remediadores deterministas para patrones acotados del MVP, verificados por reanálisis (la inyección SQL queda como detección y propuesta, sin parche automático).
- **Capa de IA opcional** (desactivada por defecto): explicaciones en lenguaje natural por hallazgo, con proveedor local **Ollama** recomendado y proveedor `stub` determinista para pruebas. La IA no aplica parches ni participa en la verificación.
- **Evaluación reproducible** sobre corpus etiquetado: `python -m app.services.evaluation` (recall 0,875; especificidad 1,000; 0 falsos positivos en el corpus de control).

## Estructura del repositorio

| Ruta | Contenido |
|------|-----------|
| `app/` | Backend FastAPI: servicios de análisis, parsers, clasificación, remediadores, verificadores, capa IA y consola web |
| `tests/` | Suite de pruebas (pytest); 281 pruebas con cobertura ~94 % sobre `app/` |
| `fixtures/mvp/` | Corpus controlado de ejemplos vulnerables del MVP |
| `fixtures/eval/` | Corpus de evaluación (casos limpios y verdad de referencia) |
| `reports/` | Informes SAST de ejemplo y generados en runtime |
| `scripts/` | Scripts de apoyo al desarrollo |
| `videos/` | Vídeos de demostración (instalación, despliegue y uso) |

## Stack

- Python 3.12+
- FastAPI, Uvicorn, Jinja2
- Bandit, Semgrep
- pytest, pytest-cov, httpx (tests)
- Ruff (lint), pre-commit (opcional local)
- GitHub Actions (CI)
- Ollama (opcional, IA local)

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

`bandit` y `semgrep` deben ser invocables por el backend (subprocesos). Semgrep puede necesitar **red** la primera vez para descargar reglas. En Windows, Semgrep no tiene soporte nativo: se recomienda trabajar bajo **WSL**.

## Ejecutar la aplicación

```bash
uvicorn app.main:app --reload
```

Opcional: copia `.env.example` a `.env` en la raíz del repo (IA, límites ZIP, etc.). El backend **carga `.env` al arrancar**; las variables ya exportadas en la shell o en systemd tienen prioridad.

Por defecto los resultados de análisis viven solo en memoria. Para que **sobrevivan a reinicios** (enlaces `/results/{id}` y `/report` persistentes), define `TFG_SCAN_STORE_DIR` (p. ej. `var/scans`); se guarda un `.json` por análisis y se purgan por TTL (`TFG_SCAN_STORE_TTL_SEC`, 7 días) y número máximo (`TFG_SCAN_STORE_MAX_ENTRIES`, 200).

Rutas principales:

- Inicio: `http://127.0.0.1:8000/` — presentación y acceso al formulario de análisis
- Nuevo análisis: `http://127.0.0.1:8000/analyze` (la ruta `/dashboard` redirige aquí)
- Resultados: `http://127.0.0.1:8000/results/{analysis_id}` — con filtros de vista y enriquecimiento IA
- Consola anterior con los modos de demostración sobre fixtures: `http://127.0.0.1:8000/dashboard-legacy`
- Salud: `GET /health` · Estado y límites: `GET /ai/status` · OpenAPI: `/docs`

### Consola web

El formulario principal (`/analyze`) ofrece los tres modos de análisis de proyectos **reales**:

- subida **ZIP** (para probar rápido, puedes comprimir `fixtures/mvp/` en un `.zip`);
- **clonado Git HTTPS** de hosts permitidos;
- **ruta local** relativa bajo `TFG_LOCAL_ANALYSIS_ROOT` (si está habilitado `TFG_ENABLE_LOCAL_PATH`).

La vista de resultados muestra resúmenes por severidad, categoría y modo de remediación, con `analysis_id` para trazabilidad, y permite ajustar la vista sin repetir el análisis: ocultar avisos informativos (`hide_info`) y agrupar hallazgos equivalentes (`group_equivalent`).

Los modos **MVP/demo** (informes guardados del corpus y re-ejecución runtime sobre fixtures) se conservan en `/dashboard-legacy` y en la API.

### API de análisis

- `POST /analysis/upload-zip` — fichero `multipart/form-data` (campo `file`). Límite por defecto ~20 MB (`TFG_ZIP_MAX_BYTES`).
- `POST /analysis/git-clone` — JSON `{"url": "https://github.com/org/repo"}` (HTTPS, hosts permitidos por `TFG_GIT_ALLOWED_HOSTS`; desactivable con `TFG_ENABLE_GIT_CLONE=0`).
- `POST /analysis/local-path` — JSON `{"relative_path": "mi-proyecto"}`: subdirectorio **relativo** bajo `TFG_LOCAL_ANALYSIS_ROOT` (sin rutas absolutas ni `..`). Responde 403 si el modo no está permitido.
- `GET /analysis/fixtures` y `POST /analysis/run-fixtures` — modos de demostración sobre el corpus MVP.
- `POST /analysis/{analysis_id}/presentable/enrich` — añade explicaciones IA a un análisis reciente sin repetir el escaneo.

Variables útiles: `TFG_ZIP_MAX_BYTES`, `TFG_LOCAL_ANALYSIS_ROOT`, `TFG_GIT_CLONE_TIMEOUT`, `TFG_ANALYSIS_TIMEOUT_SEC` (segundos **por** invocación de Bandit y de Semgrep; por defecto 600; `0` = sin límite), `TFG_ANALYSIS_EXCLUDE_DIRS` (directorios o globs excluidos del análisis).

**`.semgrepignore`:** si el proyecto analizado incluye un fichero `.semgrepignore` en su raíz (p. ej. tras un `git clone`), **Semgrep lo respeta** además de las exclusiones que añade el backend vía `--exclude`. Aplica al **código del proyecto escaneado**, no a este repositorio.

### Capa de IA (opcional)

Desactivada por defecto. Para explicaciones reales con un modelo local vía [Ollama](https://ollama.com/):

```bash
export TFG_AI_EXPLANATIONS_ENABLED=1
export TFG_AI_PROVIDER=ollama
export TFG_AI_MODEL=llama3.2:3b
export TFG_AI_OLLAMA_URL=http://127.0.0.1:11434
```

Para pruebas sin red ni modelo: `TFG_AI_PROVIDER=stub`. Cada explicación conserva metadatos de trazabilidad (proveedor, modelo, versión y hash del prompt). La IA **no** modifica código: las remediaciones verificadas proceden únicamente de los remediadores deterministas.

## Calidad de código (lint)

El proyecto usa [`ruff`](https://docs.astral.sh/ruff/) (incluido en el extra `dev`) como linter y ordenador de imports. La configuración vive en `pyproject.toml` (`[tool.ruff]`):

```bash
ruff check app tests          # detectar problemas
ruff check app tests --fix    # corregir lo autofixeable (imports, etc.)
```

## Tests

```bash
pytest -q
```

La suite usa cobertura sobre `app/` con reporte `term-missing` y umbral mínimo del **85 %** (configurado en `pyproject.toml` mediante `pytest-cov`):

```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=85
```

En CI (Ubuntu) las dependencias se instalan como en [`.github/workflows/ci.yml`](.github/workflows/ci.yml) y se aplica el mismo gate de cobertura.

## Vídeos de demostración

En [`videos/`](videos/) hay vídeos cortos que muestran el sistema en funcionamiento:

- [`instalacion-despliegue.mp4`](videos/instalacion-despliegue.mp4) — instalación desde cero (clonado, entorno virtual e instalación de dependencias) y despliegue: arranque local con `uvicorn app.main:app` y arranque en un servidor con `--host 0.0.0.0 --port 8000`, accediendo después vía `http://<ip-del-servidor>:8000/`.
- [`instalacion-ollama.mp4`](videos/instalacion-ollama.mp4) — instalación de [Ollama](https://ollama.com) y descarga del modelo `llama3.2:3b` para la [capa de IA opcional](#capa-de-ia-opcional), con comprobación de que el servicio responde.
- [`config+analiza-localpath.mp4`](videos/config+analiza-localpath.mp4) — configuración del `.env` desde `.env.example` (activación de la capa de IA y del análisis por ruta local con `TFG_LOCAL_ANALYSIS_ROOT`) y análisis del proyecto vulnerable de demostración (`vulnerable_demo.zip` descomprimido) mediante el modo de ruta local de la consola web.
- [`analiza-gitclone.mp4`](videos/analiza-gitclone.mp4) — análisis de un repositorio remoto mediante el modo de clonado Git HTTPS de la consola web, usando este mismo repositorio como ejemplo.
- [`demo-remediacion.mp4`](videos/demo-remediacion.mp4) — demostración del ciclo completo de remediación determinista sobre el corpus `fixtures/mvp/` con `scripts/demo_remediacion.py`: para cada fixture se muestra el fragmento vulnerable, la propuesta de corrección y la verificación por reanálisis con Bandit y Semgrep.

Los comandos ejecutados en cada vídeo están detallados en [`videos/README.md`](videos/README.md). Los pasos corresponden a las secciones [Entorno de desarrollo](#entorno-de-desarrollo) y [Ejecutar la aplicación](#ejecutar-la-aplicación).

## Licencia

Este proyecto se distribuye bajo licencia **MIT** ([`LICENSE`](LICENSE)).
