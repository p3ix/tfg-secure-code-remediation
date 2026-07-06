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
