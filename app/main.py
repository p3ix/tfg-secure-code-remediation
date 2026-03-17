from fastapi import FastAPI

app = FastAPI(
    title="TFG Secure Code Remediation",
    description="API base del TFG para análisis y remediación asistida de vulnerabilidades",
    version="0.1.0"
)

@app.get("/health")
def health():
    return {"status": "ok"}
