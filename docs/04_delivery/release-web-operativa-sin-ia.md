# Release: web operativa sin IA (hito fase 2)

## Resumen

Con las iteraciones 1–7 (dashboard real-first, contrato de errores, escaneo de proyectos grandes, observabilidad, seguridad operativa de entradas y manual de usuario), el TFG alcanza un **hito estable**: desde el navegador se puede analizar código Python real **sin activar explicaciones ni remediación asistida por modelo generativo**.

La capa IA permanece en roadmap ([ADR-002](../02_decisions/ADR-002-ai-assisted-roadmap.md)) con `TFG_AI_EXPLANATIONS_ENABLED` en `false` por defecto.

## Qué incluye este hito

### Consola web (`/dashboard`)

| Modo | Tipo | Estado |
|------|------|--------|
| Subir ZIP | Real | Operativo |
| Clonar repositorio Git (HTTPS) | Real | Operativo (sujeto a `TFG_ENABLE_GIT_CLONE` y hosts permitidos) |
| Ruta local permitida | Real | Operativo (requiere `TFG_LOCAL_ANALYSIS_ROOT` y `TFG_ENABLE_LOCAL_PATH`) |
| Informes guardados (fixtures) | MVP/demo | Operativo |
| Ejecutar fixtures (runtime) | MVP/demo | Operativo |

Opciones transversales en el formulario:

- **Vista demo** (`hide_info`)
- **Agrupar equivalentes** (`group_equivalent`)
- **Analysis ID** en resultados y errores (trazabilidad)

### API equivalente (integración / automatización)

| Endpoint | Paridad con web |
|----------|-----------------|
| `POST /analysis/upload-zip` | ZIP |
| `POST /analysis/git-clone` | Git |
| `POST /analysis/local-path` | Ruta local |
| `GET /analysis/fixtures` / presentable | Informes estáticos |
| `POST /analysis/run-fixtures` / presentable | Runtime fixtures |

### Operación y seguridad (resumen)

- Contrato de errores unificado (`error_code`, `message`, `analysis_id`) — ver [api-dashboard-error-contract.md](api-dashboard-error-contract.md).
- Límites ZIP, Git y rutas — ver [seguridad-operativa-entrada-codigo.md](seguridad-operativa-entrada-codigo.md).
- Límites de árbol grande — ver [escaneo-proyectos-grandes.md](escaneo-proyectos-grandes.md).
- Logs por etapa y `analysis_id` — ver [observabilidad-minima-operativa.md](observabilidad-minima-operativa.md).

### Documentación de usuario

- [manual-usuario-web.md](manual-usuario-web.md)

## Fuera de alcance de este hito

- Explicaciones o parches generados por LLM (`TFG_AI_EXPLANATIONS_ENABLED`).
- Autofix completo sobre proyectos reales arbitrarios (solo patrones MVP acotados en pipeline de verificación).
- Autenticación multiusuario, despliegue en producción endurecido (TLS, rate limiting global, etc.).

## Verificación manual recomendada

1. Arrancar la API: `uvicorn app.main:app --reload`.
2. Abrir `http://127.0.0.1:8000/dashboard`.
3. Comprobar que aparecen los cinco modos en «Nuevo análisis».
4. **ZIP:** subir un `.zip` pequeño con código Python; revisar hallazgos o estado vacío.
5. **Git:** URL pública `https://github.com/.../....git` (si `TFG_ENABLE_GIT_CLONE=1`).
6. **Local:** con `TFG_LOCAL_ANALYSIS_ROOT` apuntando a un directorio de prueba, analizar un subdirectorio relativo.
7. **Fixtures:** ejecutar «Informes guardados» y «Ejecutar fixtures» para validar el entorno Bandit/Semgrep.
8. Consultar `GET /ai/status` y confirmar `ai_explanations_enabled: false` en entorno por defecto.

## Verificación automatizada

```bash
.venv/bin/pytest -q tests/test_web_release_smoke.py tests/test_dashboard.py
.venv/bin/pytest -q
```

Los tests de humo comprueban presencia de modos en HTML, paridad mínima de endpoints y que la IA no es requisito del estado por defecto.

## Iteraciones que componen el hito

| # | Tema | Documento |
|---|------|-----------|
| 1 | Git en dashboard | [dashboard-git-clone-web.md](dashboard-git-clone-web.md) |
| 2 | Dashboard real-first | [dashboard-real-first.md](dashboard-real-first.md) |
| 3 | Contrato de errores | [api-dashboard-error-contract.md](api-dashboard-error-contract.md) |
| 4 | Proyectos grandes | [escaneo-proyectos-grandes.md](escaneo-proyectos-grandes.md) |
| 5 | Observabilidad | [observabilidad-minima-operativa.md](observabilidad-minima-operativa.md) |
| 6 | Seguridad entradas | [seguridad-operativa-entrada-codigo.md](seguridad-operativa-entrada-codigo.md) |
| 7 | Manual usuario | [manual-usuario-web.md](manual-usuario-web.md) |
| 8 | Este release | Este documento |

## Siguiente fase

Integración de la **capa IA** (explicaciones / asistencia) sobre el núcleo de análisis ya operativo, manteniendo supervisión humana y flags de entorno.

---

*Hito cerrado como entrega del TFG — fase «análisis real vía web sin IA».*
