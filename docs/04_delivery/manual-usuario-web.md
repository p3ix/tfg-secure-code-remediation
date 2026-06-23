# Manual de usuario: interfaz web v2

Este documento describe, desde el punto de vista de quien usa la aplicación en el navegador, cómo lanzar análisis de código Python con Bandit y Semgrep y cómo interpretar la salida. Lo he redactado en paralelo al rediseño web v2 del TFG para la defensa y el despliegue en VPS.

## 1. Pantallas principales

La interfaz pública se organiza en tres rutas:

| Ruta | Rol |
|------|-----|
| **`/`** | Inicio: qué hace la app, flujo en tres pasos y enlace a nuevo análisis |
| **`/analyze`** | Formulario para lanzar un escaneo (solo modos reales) |
| **`/results/{analysis_id}`** | Resultados del análisis en una página dedicada |

**URL habitual en local:** `http://127.0.0.1:8000/`

La ruta antigua `/dashboard` redirige a `/analyze`. Los modos demo basados en fixtures del corpus MVP siguen disponibles para desarrollo en `/dashboard-legacy`, pero no forman parte de la experiencia pública de defensa.

## 2. Requisitos

- Un navegador actual.
- El backend en ejecución (por ejemplo `uvicorn app.main:app`).
- En el **servidor** donde corre el análisis: herramientas `bandit` y `semgrep` disponibles para el proceso. La primera ejecución de Semgrep puede requerir **descarga de reglas** según el entorno.

### Activar explicaciones IA

Por defecto la IA está desactivada. Para ver el toggle en el formulario o el botón de enriquecimiento en resultados:

```bash
TFG_AI_EXPLANATIONS_ENABLED=1 TFG_AI_PROVIDER=stub uvicorn app.main:app --host 127.0.0.1 --port 8000
```

En producción (VPS) se configura en `.env`. Con `stub` no hace falta Ollama; con `ollama` se usa un modelo local.

## 3. Flujo recomendado para la defensa

1. Abrir **`/`** y pulsar **Nuevo análisis**.
2. En **`/analyze`**, elegir **Subir ZIP** y seleccionar `vulnerable_demo.zip` (incluido en la raíz del repositorio para pruebas).
3. Opcional: marcar **Incluir explicaciones IA** o dejarlo sin marcar y añadirlas después en resultados.
4. Pulsar **Lanzar análisis**. Tras unos segundos se redirige a **`/results/{analysis_id}`**.
5. Revisar resumen, diagnóstico Bandit/Semgrep y listado de hallazgos. Si el análisis fue sin IA, usar **Añadir explicaciones IA a este resultado**.

## 4. Formulario de análisis (`/analyze`)

Formulario **POST** a `/analyze` con **multipart/form-data** (necesario para subir ficheros ZIP).

### 4.1 Origen del código

- **Subir ZIP:** proyecto comprimido. Solo se muestra el campo de fichero cuando este modo está seleccionado.
- **Clonar repositorio Git:** URL HTTPS; hosts permitidos según `TFG_GIT_ALLOWED_HOSTS`.
- **Ruta local permitida:** subdirectorio relativo bajo `TFG_LOCAL_ANALYSIS_ROOT` en el servidor.

### 4.2 Opciones de vista

- **Ocultar informativos / baja severidad:** reduce ruido en el listado.
- **Agrupar equivalentes:** fusiona hallazgos con mismo fichero, línea y categoría MVP.
- **Incluir explicaciones IA** (si está habilitada en el servidor): genera explicaciones durante el escaneo.

Al enviar el formulario, el botón muestra estado de carga (`Analizando…`) y un mensaje de progreso accesible.

## 5. Página de resultados (`/results/{analysis_id}`)

Tras un análisis correcto se muestra:

- **Objetivo** (`analysis_target`): qué se ha analizado.
- **Modo de ejecución:** p. ej. `runtime`.
- **Analysis ID:** identificador único (útil para logs y API).
- **Resúmenes:** totales por severidad, categoría MVP y modo de remediación.
- **Diagnóstico Bandit / Semgrep:** estado de cada herramienta.
- **Tabla de hallazgos:** severidad, fichero, líneas, herramienta/regla, mensaje y, si aplica, bloque de explicación IA.

Los resultados se guardan en memoria del proceso (~60 minutos). Si el identificador expiró o el servidor se reinició, la página muestra un error claro con código `[SCAN_RESULT_EXPIRED]`.

### Enriquecimiento IA posterior (WEB-5)

Si el análisis se lanzó **sin** IA, aparece un panel para **añadir explicaciones** sin volver a ejecutar Bandit ni Semgrep.

## 6. Mensajes de error

Si algo falla, aparece un bloque con el formato:

`[CÓDIGO_DE_ERROR] mensaje explicativo (analysis_id=…)`

El código coincide con el contrato de errores de la API.

## 7. Configuración visible en pantalla

| Variable | Efecto en la interfaz |
|----------|------------------------|
| `TFG_ZIP_MAX_BYTES` | Tamaño máximo del ZIP (modo Subir ZIP). |
| `TFG_ENABLE_GIT_CLONE` | Habilita o deshabilita clon Git. |
| `TFG_GIT_ALLOWED_HOSTS` | Hosts listados en la tarjeta Git. |
| `TFG_LOCAL_ANALYSIS_ROOT` | Raíz para ruta local. |
| `TFG_ENABLE_LOCAL_PATH` | Kill-switch del modo ruta local. |
| `TFG_AI_EXPLANATIONS_ENABLED` | Muestra opciones y botón de IA. |

Consulta rápida: `GET /ai/status` devuelve flags y límites en JSON.

## 8. API y documentación técnica

- **OpenAPI:** `http://127.0.0.1:8000/docs`
- Endpoints equivalentes: `POST /analysis/upload-zip`, `POST /analysis/git-clone`, `POST /analysis/local-path`, presentable y enrich.

## 9. Limitaciones conocidas

- La capa de explicación IA es opcional; el núcleo SAST no depende de ella.
- Los parches automáticos cubren patrones MVP concretos; la web prioriza visibilidad del escaneo.
- El informe exportable imprimible está previsto en una fase posterior (`/results/{id}/report`).

---

*Material de entrega del TFG. Rutas y capturas alineadas con ADR-004 (web v2).*
