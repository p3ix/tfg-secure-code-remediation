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
