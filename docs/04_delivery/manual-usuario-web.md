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

En producción (VPS) se configura en `.env` en la raíz del proyecto; el backend lo carga al arrancar. Con `stub` no hace falta Ollama; con `ollama` se usa un modelo local.

## 3. Flujo recomendado para la defensa

1. Abrir **`/`** y pulsar **Nuevo análisis**.
2. En **`/analyze`**, elegir **Subir ZIP** y seleccionar `vulnerable_demo.zip` (incluido en la raíz del repositorio para pruebas).
3. Opcional: marcar **Incluir explicaciones IA** o dejarlo sin marcar y añadirlas después en resultados.
4. Pulsar **Lanzar análisis**. Tras unos segundos se redirige a **`/results/{analysis_id}`**.
5. Revisar resumen, índice de hallazgos, diagnóstico Bandit/Semgrep y detalle. Si el análisis fue sin IA, usar **Añadir explicaciones IA** en la barra lateral.

## 4. Formulario de análisis (`/analyze`)

Formulario **POST** a `/analyze` con **multipart/form-data** (necesario para subir ficheros ZIP).

### 4.1 Origen del código

- **Subir ZIP:** proyecto comprimido. Solo se muestra el campo de fichero cuando este modo está seleccionado.
- **Clonar repositorio Git:** URL HTTPS; hosts permitidos según `TFG_GIT_ALLOWED_HOSTS`.
- **Ruta local permitida:** subdirectorio relativo bajo `TFG_LOCAL_ANALYSIS_ROOT` en el servidor.

### 4.2 Explicaciones IA

Sección dedicada en el formulario:

- Si `TFG_AI_EXPLANATIONS_ENABLED=1`, aparece el toggle **Incluir explicaciones IA en este escaneo** con texto según el proveedor (`stub` u `ollama`).
- Si la capa está desactivada, se muestra un aviso claro; el SAST funciona igual sin IA.
- Sin marcar el toggle, el análisis es más rápido y puedes usar **Añadir explicaciones IA** en la página de resultados (WEB-5).

Al enviar el formulario, el botón muestra estado de carga (`Analizando…`) y un mensaje de progreso accesible; si IA está marcada, el mensaje indica que puede tardar más (especialmente con Ollama).

## 5. Página de resultados (`/results/{analysis_id}`)

Tras un análisis correcto se muestra:

- **Banner de estado IA:** indica si el escaneo incluyó IA, si está pendiente de enrich o si la capa está desactivada en el servidor.
- **Filtros de vista:** selects para ocultar baja severidad o agrupar equivalentes **sin re-ejecutar** Bandit/Semgrep. La URL incluye `?hide_info=true&group_equivalent=true` para compartir la vista.
- **Layout en dos columnas (escritorio):** barra lateral con metadatos, totales, filtros e índice de hallazgos; panel principal con el detalle y scroll independiente.
- **Índice navegable:** enlaces a cada hallazgo (`#finding-1`, …).

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
- El informe exportable imprimible está en `/results/{analysis_id}/report` (botón «Imprimir / guardar PDF» del navegador).
- JSON completo: `/results/{analysis_id}/export.json` (enlace «Exportar JSON» en resultados).

---

*Material de entrega del TFG. Rutas y capturas alineadas con ADR-004 (web v2).*
