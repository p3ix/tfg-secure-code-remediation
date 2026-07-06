# Vídeos de demostración

## `instalacion-despliegue.mp4`

Instalación desde cero y despliegue de la aplicación. Comandos ejecutados en el vídeo:

```bash
# Clonado del repositorio
git clone https://github.com/p3ix/tfg-secure-code-remediation.git

# Entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalación de dependencias
pip install -U pip
pip install -e ".[dev]"

# Arranque local (escucha solo en 127.0.0.1)
uvicorn app.main:app

# Arranque en servidor/VPS (escucha en todas las interfaces)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Al desplegar en un VPS, la aplicación queda accesible desde el navegador en `http://<ip-del-servidor>:8000/` (en el vídeo, `http://158.220.125.114:8000/`). El arranque local sin `--host` solo acepta conexiones desde la propia máquina.

## `instalacion-ollama.mp4`

Instalación de [Ollama](https://ollama.com) y del modelo local usado por la capa de IA opcional. Comandos ejecutados en el vídeo:

```bash
# Instalación de Ollama (crea y arranca el servicio)
curl -fsSL https://ollama.com/install.sh | sh

# Descarga del modelo usado por la capa de IA
ollama pull llama3.2:3b

# Comprobación de que el servicio responde
curl http://127.0.0.1:11434/api/version
```

Con Ollama en marcha, la capa de IA se activa en el `.env` de la aplicación (`TFG_AI_EXPLANATIONS_ENABLED=1`, proveedor `ollama`); su estado puede consultarse en `GET /ai/status`. Ollama escucha solo en `127.0.0.1:11434` y no debe exponerse al exterior.

## `config+analiza-localpath.mp4`

Configuración de la aplicación desde la plantilla `.env.example` y análisis de un proyecto vulnerable mediante el modo de ruta local. Comandos ejecutados en el vídeo:

```bash
# Descomprimir el proyecto vulnerable de demostración (crea la carpeta vulnerable_app/)
unzip vulnerable_demo.zip

# Crear la configuración desde la plantilla y editarla
cp .env.example .env
nano .env
```

Variables ajustadas en el `.env` durante el vídeo:

```bash
# Activar las explicaciones asistidas por IA (requiere Ollama en marcha)
TFG_AI_EXPLANATIONS_ENABLED=1

# Directorio raíz permitido para el análisis por ruta local;
# sin este valor, el modo aparece deshabilitado en el formulario
TFG_LOCAL_ANALYSIS_ROOT=/home/p3i/tfg-secure-code-remediation
```

Tras reiniciar `uvicorn` (el `.env` se carga al arrancar), en el formulario de `/analyze` se selecciona el modo **ruta local** y se indica la ruta relativa `vulnerable_app`. La aplicación analiza el directorio con Bandit y Semgrep y muestra los hallazgos normalizados con sus explicaciones asistidas por IA. Solo pueden analizarse subdirectorios dentro de `TFG_LOCAL_ANALYSIS_ROOT`; las rutas absolutas o con `..` se rechazan.

## `analiza-gitclone.mp4`

Análisis de un repositorio remoto mediante el modo de **clonado Git HTTPS** de la consola web. En el formulario de `/analyze` se selecciona el modo Git y se introduce la URL del repositorio (en el vídeo, este mismo proyecto):

```
https://github.com/p3ix/tfg-secure-code-remediation.git
```

La aplicación clona el repositorio en un directorio temporal, lo analiza con Bandit y Semgrep y muestra los resultados; el clon se descarta al terminar. Solo se aceptan URLs HTTPS de los hosts permitidos (`TFG_GIT_ALLOWED_HOSTS`, por defecto `github.com` y `gitlab.com`).
