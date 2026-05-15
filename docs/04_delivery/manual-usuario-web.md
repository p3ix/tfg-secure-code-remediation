# Manual de usuario: consola web del análisis (`/dashboard`)

Este documento recoge, desde el punto de vista de quien usa la aplicación en el navegador, cómo lanzar análisis de código Python con Bandit y Semgrep y cómo interpretar la salida. Lo he redactado en paralelo al desarrollo de la consola web del TFG para poder citarlo en la memoria como material de entrega y de apoyo a demostraciones.

## 1. Qué es el dashboard

El **dashboard** es una página HTML servida por la propia API (FastAPI + Jinja2). Permite:

- ejecutar análisis **reales** sobre proyectos aportados como ZIP, clon Git HTTPS o ruta local permitida en el servidor;
- usar modos **MVP/demo** basados en el corpus interno `fixtures/mvp` para validación rápida;
- ver el resultado en formato **presentable**: hallazgos normalizados, sin volcado crudo de herramienta, pensado para revisión y para material de memoria.

**URL habitual:** `http://127.0.0.1:8000/dashboard` (si la API corre en el puerto por defecto).

La raíz `http://127.0.0.1:8000/` redirige a `/dashboard`.

## 2. Requisitos

- Un navegador actual.
- El backend en ejecución (por ejemplo `uvicorn app.main:app`).
- En el **servidor** donde corre el análisis: herramientas `bandit` y `semgrep` disponibles para el proceso (el backend las invoca por subproceso). La primera ejecución de Semgrep puede requerir **descarga de reglas** según el entorno.

## 3. Estructura de la pantalla

### 3.1 Panel «Nuevo análisis»

Formulario **POST** a `/dashboard/analyze` con **multipart/form-data** (necesario para subir ficheros ZIP).

- **Modo de análisis** (radio): determina qué origen de código se usa.
- **Archivo ZIP:** solo aplica al modo «Subir ZIP».
- **Ruta relativa:** solo aplica al modo «Ruta local permitida».
- **URL Git HTTPS:** solo aplica al modo «Clonar repositorio Git».
- **Vista presentable:**
  - **Vista demo** (`hide_info`): reduce el listado ocultando parte de hallazgos informativos o de menor severidad (comportamiento descrito en la propia interfaz).
  - **Agrupar equivalentes** (`group_equivalent`): fusiona hallazgos que coinciden en fichero, línea y categoría MVP, mostrando varias fuentes en una misma fila cuando aplica.

### 3.2 Panel de resultados

Tras un análisis correcto se muestra:

- **Objetivo** (`analysis_target`): qué se ha analizado (por ejemplo etiqueta del ZIP, prefijo `git:https://…`, `local:subruta/...`).
- **Modo de ejecución:** p. ej. `runtime` cuando el escaneo se ha ejecutado contra código extraído o clonado.
- **Analysis ID:** identificador único de la ejecución (útil para correlacionar con logs del servidor).
- **Resúmenes:** totales por severidad, categoría MVP y modo de remediación.
- **Tabla de hallazgos:** cada fila incluye severidad, fichero, líneas, herramienta/regla y texto de mensaje acotado.

Si el análisis termina sin filas visibles con los filtros activos, la interfaz indica explícitamente un estado vacío.

### 3.3 Mensajes de error

Si algo falla, aparece un bloque de error con el formato:

`[CÓDIGO_DE_ERROR] mensaje explicativo (analysis_id=…)`

El **código** coincide con el contrato de errores de la API para los mismos flujos, de modo que la documentación técnica y la experiencia web están alineadas.

## 4. Modos de análisis (orden recomendado en la interfaz)

| Modo | Tipo | Qué hace |
|------|------|----------|
| **Subir ZIP (real)** | Producción | Sube un `.zip` con el proyecto. El servidor valida tipo/firma, tamaño y extracción segura y ejecuta Bandit + Semgrep. |
| **Clonar repositorio Git (real)** | Producción | Clonado superficial (`--depth 1`) desde **HTTPS**; solo hosts permitidos por configuración. |
| **Ruta local permitida (real)** | Producción | Analiza un **subdirectorio relativo** bajo una raíz fijada en el servidor. No se aceptan rutas absolutas ni `..`. |
| **Informes guardados (MVP/demo)** | Demo | Carga informes ya generados del corpus MVP (sin ejecutar herramientas sobre tu ZIP). |
| **Ejecutar fixtures (MVP/demo)** | Demo | Ejecuta Bandit y Semgrep sobre el directorio interno `fixtures/mvp` (útil para comprobar que el entorno funciona). |

Los modos «real» están pensados para trabajo con proyectos ajenos; los «MVP/demo» priorizan repetibilidad y demostración académica.

## 5. Buenas prácticas rápidas

- **ZIP:** usar archivo `.zip` estándar; el límite en bytes se muestra en la tarjeta del modo (proviene de `TFG_ZIP_MAX_BYTES`).
- **Git:** usar URL pública `https://host/organización/repositorio(.git)` sin credenciales en la URL, sin query ni fragmento; el host debe estar entre los permitidos (por defecto se muestran en la tarjeta).
- **Ruta local:** escribir solo la parte relativa, p. ej. `mi-proyecto` o `grupo/proyecto`, nunca rutas absolutas. Si el modo aparece deshabilitado, es porque falta configurar la raíz en el servidor o porque el administrador ha desactivado el análisis local.
- **Seguridad:** estos análisis ejecutan herramientas y procesan código no confiable; el despliegue debe aislarse y acotarse según la política del entorno (véase documentación de hardening en `docs/04_delivery/`).

## 6. Configuración que afecta a lo que ves en pantalla

El comportamiento visible depende de variables de entorno `TFG_*` en el servidor. No hace falta conocerlas todas para usar el dashboard; las decisivas son:

| Variable | Efecto en la interfaz |
|----------|------------------------|
| `TFG_ZIP_MAX_BYTES` | Tamaño máximo del ZIP subido. Aparece como «Límite actual» en el modo ZIP. |
| `TFG_ENABLE_GIT_CLONE` | Si está desactivada, el modo Git queda deshabilitado y se explica en la tarjeta. |
| `TFG_GIT_ALLOWED_HOSTS` | Hosts HTTPS permitidos para clonar; se listan en la tarjeta del modo Git. |
| `TFG_LOCAL_ANALYSIS_ROOT` | Directorio base del servidor para el modo ruta local. |
| `TFG_ENABLE_LOCAL_PATH` | Si está desactivada, el modo ruta local queda deshabilitado aunque exista raíz. |

Existen límites adicionales (entradas máximas del ZIP, árbol demasiado grande, tiempo por herramienta, etc.) descritos en la documentación de entrega de robustez y seguridad operativa.

**Consulta rápida para operadores:** `GET /ai/status` devuelve un resumen JSON de flags y límites actuales (incluye campos como `zip_max_bytes`, `zip_max_entries`, `local_path_enabled`, `enable_local_path`, entre otros).

## 7. Dónde ir si necesitas la API cruda

- **Documentación interactiva OpenAPI:** `http://127.0.0.1:8000/docs`
- Endpoints de análisis equivalentes a los modos web: `POST /analysis/upload-zip`, `POST /analysis/git-clone`, `POST /analysis/local-path`.

El manual de interfaz se centra en `/dashboard`; la integración vía HTTP queda documentada en el propio OpenAPI y en los entregables de contrato de errores (`docs/04_delivery/api-dashboard-error-contract.md`).

## 8. Limitaciones conocidas (alcance TFG)

- La capa de **explicación asistida por IA** es opcional y puede figurar desactivada; el núcleo de detección no depende de ella (ver ADR-002 en el repositorio).
- Los parches automáticos y la verificación asociada cubren **patrones MVP** concretos; el dashboard prioriza **visibilidad del escaneo** sobre un IDE completo.

---

*Documento generado como material de entrega del TFG y guía de usuario de la consola web; convive con la documentación técnica del proyecto en `docs/`.*
