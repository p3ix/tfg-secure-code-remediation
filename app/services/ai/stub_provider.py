from __future__ import annotations

from app.models.ai_explanation import AIExplanation
from app.models.finding import NormalizedFinding
from app.services.ai.enrichment import apply_finding_enrichment
from app.services.ai.provider import PROMPT_VERSION

STUB_MODEL = "stub-deterministic"

# Texto fijo por categoría MVP: determinista, sin red ni clave. Permite cablear el
# contrato extremo a extremo y mantener la suite/CI offline (ADR-003).
_CATEGORY_TEXT: dict[str, dict[str, object]] = {
    "command_injection": {
        "summary": "Ejecución de comandos del sistema con entrada potencialmente no confiable.",
        "risk": "Un atacante podría inyectar comandos arbitrarios (CWE-78) y comprometer el host.",
        "suggestion": "Evita shell=True; usa listas de argumentos y valida/escapa la entrada.",
        "action_steps": [
            "Localiza la llamada a subprocess/os.system en la línea indicada.",
            "Sustituye shell=True por una lista de argumentos sin invocar el shell.",
            "Valida o restringe la entrada del usuario antes de ejecutar el comando.",
        ],
    },
    "yaml_load": {
        "summary": "Deserialización insegura de YAML que puede instanciar objetos arbitrarios.",
        "risk": "Carga de YAML no confiable puede derivar en ejecución de código (CWE-20/502).",
        "suggestion": "Usa yaml.safe_load en lugar de yaml.load sin Loader seguro.",
        "action_steps": [
            "Revisa el punto de carga YAML señalado en el hallazgo.",
            "Cambia yaml.load por yaml.safe_load (o un Loader explícito y seguro).",
            "Evita deserializar YAML procedente de fuentes no confiables.",
        ],
    },
    "flask_debug": {
        "summary": "Servidor Flask ejecutándose con el modo debug activado.",
        "risk": "El depurador expone una consola interactiva y datos sensibles (CWE-489).",
        "suggestion": "Desactiva debug en producción y controla el entorno por configuración.",
        "action_steps": [
            "Comprueba si app.run(debug=True) o FLASK_DEBUG están activos en el fichero.",
            "Desactiva debug en entornos de despliegue y usa variables de entorno.",
            "Ejecuta con un servidor WSGI/ASGI en producción (gunicorn, waitress, etc.).",
        ],
    },
    "requests_timeout": {
        "summary": "Petición HTTP sin timeout explícito.",
        "risk": "Una respuesta lenta puede bloquear el proceso indefinidamente (CWE-400).",
        "suggestion": "Pasa siempre el parámetro timeout a las llamadas de requests.",
        "action_steps": [
            "Identifica la llamada requests.get/post sin timeout en la línea señalada.",
            "Añade timeout con un valor razonable (p. ej. connect=5, read=30).",
            "Maneja requests.exceptions.Timeout para degradar con mensaje claro.",
        ],
    },
    "verify_false": {
        "summary": "Verificación de certificados TLS desactivada.",
        "risk": "Permite ataques man-in-the-middle al no validar el certificado (CWE-295).",
        "suggestion": "No uses verify=False; confía en la CA del sistema o aporta el bundle correcto.",
        "action_steps": [
            "Busca verify=False en la petición HTTP del hallazgo.",
            "Elimina verify=False y usa el bundle de CA del sistema.",
            "Si hay CA interna, configura verify con la ruta al certificado de confianza.",
        ],
    },
}

_DEFAULT_TEXT = {
    "summary": "Hallazgo de seguridad detectado por el análisis estático.",
    "risk": "Revisa el impacto según la categoría y el estándar (CWE/OWASP) asociado.",
    "suggestion": "Aplica la práctica segura recomendada para este tipo de hallazgo.",
    "action_steps": [
        "Revisa el fichero y la línea indicados en el hallazgo.",
        "Consulta la documentación de la regla y el CWE asociado.",
        "Aplica la remediación y vuelve a ejecutar el análisis estático.",
    ],
}


class StubProvider:
    """Proveedor determinista para tests, CI y demo offline (ADR-003)."""

    name = "stub"
    model = STUB_MODEL

    def explain(self, finding: NormalizedFinding) -> AIExplanation:
        text = _CATEGORY_TEXT.get(finding.mvp_category, _DEFAULT_TEXT)
        steps = text.get("action_steps", _DEFAULT_TEXT["action_steps"])
        explanation = AIExplanation(
            summary=str(text["summary"]),
            risk=str(text["risk"]),
            suggestion=str(text["suggestion"]),
            provider=self.name,
            model=STUB_MODEL,
            prompt_version=PROMPT_VERSION,
            cached=False,
            action_steps=[str(step) for step in steps],  # type: ignore[arg-type]
        )
        return apply_finding_enrichment(explanation, finding)
