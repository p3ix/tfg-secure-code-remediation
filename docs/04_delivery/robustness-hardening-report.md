# Informe de robustez y hardening (A1-D2)

## Objetivo de la iteracion

Mantener el alcance funcional del proyecto y reforzar su robustez en cuatro frentes: contratos API, hardening operativo, consistencia de pipeline y estabilidad del dashboard.

## Cambios ejecutados por bloque

### A - API y contratos

- `POST /analysis/upload-zip`
  - Validacion de fichero vacio y extension `.zip`.
  - Respuesta `413` para payload demasiado grande (`PayloadTooLargeError`).
- `POST /analysis/git-clone`
  - Validacion mas estricta de URL HTTPS (sin credenciales, sin query/fragment, formato owner/repo).
  - Error explicito en timeout de clonacion.
- `POST /analysis/local-path`
  - Validacion adicional de ruta en dashboard (`local_path` obligatorio en su modo).
  - Endurecimiento de resolucion para evitar rutas ambiguas.
- Endpoints presentables
  - Tolerancia a hallazgos invalidos en conversion interna -> presentable.
  - Metadato `invalid_findings_skipped` para trazabilidad de contrato.
- Pipeline endpoint
  - El roundtrip de verificadores ahora reporta resumen y degradacion parcial sin abortar toda la ejecucion.

### B - Hardening de seguridad operativa

- Extraccion ZIP endurecida:
  - rechazo de ZIP invalido o vacio;
  - limite de numero de entradas (`max_entries`);
  - mantenimiento de defensa path traversal y limite descomprimido.
- Subprocesos de analisis:
  - manejo explicito de comando ausente (`FileNotFoundError`);
  - timeout robusto con mensaje accionable;
  - `stderr_preview` en metadatos de ejecucion para diagnostico.
- Configuracion de entorno:
  - parseo robusto de enteros, booleanos, CSV y hosts permitidos;
  - validacion de rangos y formatos en `Settings`.

### C - Pipeline y calidad de resultados

- Salida `presentable` mas resiliente:
  - fallback de claves vacias (`unknown`, `detection_only`);
  - conversion defensiva de filas invalidas.
- Pipeline de verificacion MVP:
  - resumen agregado por categorias/fixtures;
  - errores por fixture y por categoria sin interrumpir lotes restantes.

### D - Dashboard robusto

- Validacion de entradas por modo (`upload_zip`, `local_path`).
- Estado visual explicito para ejecuciones sin hallazgos.
- Nota visual cuando se omiten findings invalidos por contrato incompleto.

## Evidencia de pruebas

- Suite ejecutada con entorno virtual del proyecto:
  - `121 passed in 3.90s`
  - cobertura total: `87.76%`
- Pruebas nuevas o ampliadas en:
  - `tests/test_config.py`
  - `tests/test_project_scan_service.py`
  - `tests/test_runtime_analysis_service.py`
  - `tests/test_presentable_scan.py`
  - `tests/test_pipeline_orchestrator.py`
  - `tests/test_dashboard.py`
  - `tests/test_mvp_autofix_verification_endpoint.py`

## Resultado

Se cierra la iteracion de robustez sin ampliar alcance funcional: se mejora comportamiento ante casos borde, seguridad operativa, consistencia de contratos y resiliencia de interfaz.
