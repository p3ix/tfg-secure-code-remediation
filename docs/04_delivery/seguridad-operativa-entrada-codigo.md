# Avance: seguridad operativa de entrada de código

## Objetivo

Reducir la superficie de abuso en las entradas que incorporan código al análisis (ZIP, URL Git HTTPS, rutas locales), mediante límites explícitos, kill-switches por variable de entorno y validaciones simples de formato, alineadas con despliegues operativos del TFG.

## Cambios implementados

### Configuración (`app/config.py`)

| Variable | Rol |
|----------|-----|
| `TFG_ZIP_MAX_ENTRIES` | Máximo de entradas en el índice ZIP antes de extraer (anti abuso / zip bomb lógico). Por defecto `10000`. |
| `TFG_ZIP_MAX_UNCOMPRESSED_BYTES` | Tope de bytes descomprimidos; el valor efectivo sigue siendo `min(TFG_ZIP_MAX_BYTES * 5, este tope)`. Por defecto 100 MiB. |
| `TFG_GIT_URL_MAX_LENGTH` | Longitud máxima de la URL de clonado. Por defecto `2048`. |
| `TFG_LOCAL_PATH_MAX_LENGTH` | Longitud máxima de la ruta relativa local. Por defecto `4096`. |
| `TFG_ENABLE_LOCAL_PATH` | Kill-switch: si es `0`/`false`, el análisis por ruta local queda desactivado aunque exista `TFG_LOCAL_ANALYSIS_ROOT`. Por defecto habilitado. |

### Servicio (`app/services/project_scan_service.py`)

- Validación de longitud de URL Git antes del resto de reglas HTTPS/host.
- Validación de longitud de ruta relativa y rechazo de caracteres de control (ASCII &lt; 32).
- Extracción ZIP usa `zip_max_entries` y el tope de descompresión configurable.

### API y dashboard (`app/main.py`, `app/templates/dashboard.html`)

- `POST /analysis/local-path` comprueba primero `TFG_ENABLE_LOCAL_PATH`, luego la presencia de raíz local.
- El dashboard distingue en la ayuda del modo local: raíz no configurada vs desactivación explícita por `TFG_ENABLE_LOCAL_PATH`.
- `GET /ai/status` expone límites y flags relevantes para operadores.

### Contrato de errores

Nuevos códigos de error en `detail.error_code` para algunos fallos de ZIP:

- `ZIP_TOO_MANY_ENTRIES`
- `ZIP_DECOMPRESSED_TOO_LARGE`

(El resto mantiene el mapeo existente; rutas locales siguen usando `LOCAL_PATH_INVALID` cuando aplica.)

### Content-Length

No se implementó rechazo tempraro por cabecera `Content-Length` en `POST /analysis/upload-zip`: con `multipart/form-data` el tamaño del cuerpo incluye metadatos del formulario, no solo el fichero, por lo que comparar contra `TFG_ZIP_MAX_BYTES` sería incorrecto. El límite sigue aplicándose tras leer el fichero y en la extracción.

## Pruebas

- `tests/test_config.py` — defaults y lectura de nuevas variables.
- `tests/test_project_scan_service.py` — URL larga, ZIP con demasiadas entradas vía `TFG_ZIP_MAX_ENTRIES`, modo local desactivado, `/ai/status`.
- `tests/test_local_path_hardening.py` — longitud de ruta y caracteres de control.

Comando ejecutado:

```bash
.venv/bin/pytest -q
```

## Conclusión

Las entradas de código quedan acotadas de forma configurable y auditable (`/ai/status`), con un interruptor explícito para el análisis por rutas locales y validaciones que reducen vectores triviales sin cambiar el alcance funcional del análisis estático.
