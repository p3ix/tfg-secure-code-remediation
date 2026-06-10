# Índice maestro de trazabilidad (issues → entregables)

Este índice relaciona cada avance de la fase de **análisis real / web operativa sin IA** con
su issue (cuando aplica) y su documento de entrega en `docs/04_delivery/`. Sirve como mapa
único para localizar el qué/por qué de cada cambio sin recorrer todo el historial de Git.

## Análisis de proyectos reales (web y API)

| Avance | Documento de entrega |
|--------|----------------------|
| Dashboard "real-first" (modos reales priorizados) | [`dashboard-real-first.md`](dashboard-real-first.md) |
| Integración git-clone en el dashboard | [`dashboard-git-clone-web.md`](dashboard-git-clone-web.md) |
| Endurecimiento del clonado Git | [`git-clone-integration-hardening.md`](git-clone-integration-hardening.md) |
| Robustez de la subida ZIP | [`upload-zip-robustez-final.md`](upload-zip-robustez-final.md) |
| Robustez del análisis por ruta local | [`local-path-robustez-final.md`](local-path-robustez-final.md) |
| Escaneo de proyectos grandes (límites previos) | [`escaneo-proyectos-grandes.md`](escaneo-proyectos-grandes.md) |
| Cobertura y casos borde del servicio de escaneo | [`project-scan-service-cobertura-y-casos-borde.md`](project-scan-service-cobertura-y-casos-borde.md) |

## Contrato, observabilidad y seguridad operativa

| Avance | Documento de entrega |
|--------|----------------------|
| Contrato de error unificado API/dashboard | [`api-dashboard-error-contract.md`](api-dashboard-error-contract.md) |
| Observabilidad mínima (`analysis_id`, logging por etapas) | [`observabilidad-minima-operativa.md`](observabilidad-minima-operativa.md) |
| Seguridad operativa de las entradas de código | [`seguridad-operativa-entrada-codigo.md`](seguridad-operativa-entrada-codigo.md) |
| Informe global de endurecimiento (robustez) | [`robustness-hardening-report.md`](robustness-hardening-report.md) |

## Presentación de resultados y ruido

| Avance | Documento de entrega |
|--------|----------------------|
| Rutas presentables relativas al origen | [`rutas-presentables-relativas.md`](rutas-presentables-relativas.md) |
| Mapeo de categorías MVP (Bandit B404/B607) | [`mapeo-categorias-mvp-bandit.md`](mapeo-categorias-mvp-bandit.md) |
| Diagnóstico Bandit/Semgrep en el dashboard | [`diagnostico-herramientas-dashboard.md`](diagnostico-herramientas-dashboard.md) |
| Ruido y duplicados en el escaneo | [`scan-noise-and-duplicates.md`](scan-noise-and-duplicates.md) |

## Manuales, evaluación y release

| Avance | Documento de entrega |
|--------|----------------------|
| Manual de usuario de la consola web | [`manual-usuario-web.md`](manual-usuario-web.md) |
| Tabla de evaluación del MVP | [`mvp-evaluation-table.md`](mvp-evaluation-table.md) |
| Hito: web operativa sin IA | [`release-web-operativa-sin-ia.md`](release-web-operativa-sin-ia.md) |
| Barrido final de calidad sin IA | [`barrido-final-sin-ia.md`](barrido-final-sin-ia.md) ([issue](issue-barrido-final-sin-ia.md)) |
| Pulido pre-release v0.1.0 | [`issue-pulido-pre-release.md`](issue-pulido-pre-release.md) |

> Nota: la evolución narrada de todos estos avances vive en
> [`docs/07_memoria/01_evolucion_del_desarrollo.md`](../07_memoria/01_evolucion_del_desarrollo.md).
