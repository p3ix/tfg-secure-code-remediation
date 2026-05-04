# Modelo normalizado de hallazgos

## 1. Objetivo

En este documento defino un modelo normalizado de hallazgos para el TFG. El objetivo de este modelo es representar de forma homogénea los resultados obtenidos por distintas herramientas de análisis, especialmente Bandit y Semgrep, para que el sistema pueda tratarlos de manera uniforme en fases posteriores.

Este paso es importante porque el proyecto no debe limitarse a ejecutar herramientas externas y mostrar su salida sin más, sino construir una capa propia de tratamiento de hallazgos que permita:

- unificar resultados heterogéneos;
- contextualizarlos con estándares reconocidos;
- decidir si son candidatos a remediación;
- verificar cambios posteriores;
- y presentar la información de forma coherente al usuario.

## 2. Problema a resolver

Bandit y Semgrep no devuelven exactamente la misma estructura de datos.

Por ejemplo, cada herramienta utiliza:
- distintos identificadores de regla;
- diferentes nombres de campos;
- distintos niveles o convenciones de severidad;
- distinta forma de expresar el mensaje;
- y distinta riqueza de metadatos.

Si la aplicación trabajara directamente con cada formato nativo, el backend quedaría demasiado acoplado a cada herramienta y resultaría más difícil evolucionar el sistema.

Por este motivo, considero necesario definir un modelo intermedio propio, independiente de la herramienta de origen.

## 3. Objetivos del modelo

El modelo normalizado debe cumplir los siguientes objetivos:

- **homogeneidad**: representar con una misma estructura hallazgos de herramientas distintas;
- **trazabilidad**: conservar referencia suficiente al origen del hallazgo;
- **utilidad para el MVP**: incluir los campos necesarios para detección, clasificación, remediación y verificación;
- **simplicidad**: evitar un diseño excesivamente complejo para esta fase del TFG;
- **extensibilidad**: permitir añadir nuevos campos más adelante sin romper la estructura básica.

## 4. Campos mínimos necesarios

He considerado que un hallazgo normalizado del MVP debería incluir al menos la siguiente información:

- herramienta de origen;
- identificador de regla o test;
- nombre o tipo de regla;
- fichero afectado;
- línea o rango de líneas;
- mensaje descriptivo;
- severidad;
- confianza o nivel de fiabilidad, cuando exista;
- enlace o referencia al detalle técnico original, cuando exista;
- identificador CWE, si está disponible;
- categoría funcional del proyecto;
- si el hallazgo es candidato o no a remediación dentro del MVP.

## 5. Campos propuestos

### 5.1. Identificación básica
- `id`: identificador interno del hallazgo dentro del sistema
- `source_tool`: herramienta de origen (`bandit`, `semgrep`)
- `source_rule_id`: identificador original de regla o test
- `source_rule_name`: nombre original de la regla, si existe

### 5.2. Localización
- `file_path`: ruta del fichero afectado
- `line_start`: línea inicial
- `line_end`: línea final
- `code_snippet`: fragmento de código asociado, si está disponible

### 5.3. Descripción e impacto
- `title`: título corto del hallazgo
- `description`: descripción normalizada del problema
- `severity`: severidad normalizada
- `confidence`: nivel de confianza normalizado, si aplica
- `raw_message`: mensaje original devuelto por la herramienta
- `reference_url`: enlace a documentación o detalle técnico original, si existe

### 5.4. Clasificación
- `cwe_id`: identificador CWE, si existe
- `cwe_url`: enlace a la referencia CWE, si existe
- `owasp_top10`: categoría OWASP Top 10, si se asigna
- `owasp_asvs`: control o referencia ASVS, si se asigna
- `mvp_category`: categoría funcional del MVP, por ejemplo `command_injection`, `unsafe_yaml_load`, `verify_false`, `missing_timeout`, `flask_debug_true`, `sql_injection`

### 5.5. Tratamiento dentro del sistema
- `candidate_for_remediation`: indica si el hallazgo puede pasar a fase de propuesta de remediación en el MVP
- `remediation_mode`: modo previsto de tratamiento (`autofix_candidate`, `proposal_only`, `detection_only`)
- `verification_status`: estado de verificación posterior, inicialmente vacío o pendiente

### 5.6. Trazabilidad adicional
- `detected_at`: fecha u hora de detección
- `analysis_target`: conjunto analizado, por ejemplo `fixtures/mvp`
- `raw_tool_data`: bloque opcional para conservar información original no normalizada

## 6. Campos obligatorios y opcionales

### Campos obligatorios
Para el MVP considero obligatorios:

- `source_tool`
- `source_rule_id`
- `file_path`
- `line_start`
- `raw_message`
- `severity`
- `mvp_category`
- `candidate_for_remediation`
- `remediation_mode`

### Campos opcionales
Pueden ser opcionales en esta fase:

- `id`
- `source_rule_name`
- `line_end`
- `code_snippet`
- `title`
- `description`
- `confidence`
- `reference_url`
- `cwe_id`
- `cwe_url`
- `owasp_top10`
- `owasp_asvs`
- `verification_status`
- `detected_at`
- `analysis_target`
- `raw_tool_data`

La razón para dejar estos campos como opcionales es que no todas las herramientas aportan exactamente la misma información y no quiero forzar una estructura artificialmente rígida en el MVP.

## 7. Normalización de severidad y confianza

Dado que Bandit y Semgrep no expresan la severidad exactamente del mismo modo, conviene trabajar con una escala propia simple.

### Severidad normalizada propuesta
- `low`
- `medium`
- `high`

### Confianza normalizada propuesta
- `low`
- `medium`
- `high`
- `unknown`

En los casos en los que una herramienta no proporcione confianza de forma explícita, se podrá usar `unknown`.

## 8. Normalización de tratamiento en el MVP

Para alinear el modelo con el enfoque detect–repair–verify, propongo distinguir estos modos de tratamiento:

- `autofix_candidate`: casos en los que el sistema podrá proponer una remediación bastante concreta y verificable
- `proposal_only`: casos en los que se puede orientar al usuario, pero no conviene parchear automáticamente
- `detection_only`: casos detectados que en el MVP no pasarán a remediación asistida

En el estado actual del proyecto, una posible asignación sería:

- `command_injection` → `autofix_candidate` solo en algunos casos simples
- `unsafe_yaml_load` → `autofix_candidate`
- `verify_false` → `autofix_candidate`
- `missing_timeout` → `autofix_candidate`
- `flask_debug_true` → `autofix_candidate`
- `sql_injection` → `proposal_only`

## 9. Ejemplo de representación en JSON

A continuación incluyo un ejemplo de cómo podría representarse un hallazgo normalizado:

```json
{
  "id": "finding-001",
  "source_tool": "bandit",
  "source_rule_id": "B501",
  "source_rule_name": "request_with_no_cert_validation",
  "file_path": "fixtures/mvp/https_verify_false/vuln_requests_verify_false.py",
  "line_start": 4,
  "line_end": 4,
  "code_snippet": "response = requests.get(\"https://example.com\", verify=False)",
  "title": "Desactivación de verificación TLS",
  "description": "Se ha detectado una petición HTTPS con verify=False, lo que desactiva la validación de certificados.",
  "severity": "high",
  "confidence": "high",
  "raw_message": "Call to requests with verify=False disabling SSL certificate checks, security issue.",
  "reference_url": "https://bandit.readthedocs.io/en/1.9.4/plugins/b501_request_with_no_cert_validation.html",
  "cwe_id": 295,
  "cwe_url": "https://cwe.mitre.org/data/definitions/295.html",
  "owasp_top10": null,
  "owasp_asvs": null,
  "mvp_category": "verify_false",
  "candidate_for_remediation": true,
  "remediation_mode": "autofix_candidate",
  "verification_status": "pending",
  "detected_at": null,
  "analysis_target": "fixtures/mvp",
  "raw_tool_data": {}
}
```

## 10. Ejemplo de representación en Python

Una posible representación sencilla en Python podría ser mediante dataclass:

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class NormalizedFinding:
    source_tool: str
    source_rule_id: str
    file_path: str
    line_start: int
    raw_message: str
    severity: str
    mvp_category: str
    candidate_for_remediation: bool
    remediation_mode: str
    source_rule_name: str | None = None
    line_end: int | None = None
    code_snippet: str | None = None
    title: str | None = None
    description: str | None = None
    confidence: str | None = None
    reference_url: str | None = None
    cwe_id: int | None = None
    cwe_url: str | None = None
    owasp_top10: str | None = None
    owasp_asvs: str | None = None
    verification_status: str | None = None
    detected_at: str | None = None
    analysis_target: str | None = None
    raw_tool_data: dict[str, Any] | None = None
```

## 11. Justificación del diseño

Considero que este modelo es adecuado para el MVP porque equilibra simplicidad y utilidad.

Por un lado, conserva la información más importante del hallazgo original y mantiene trazabilidad hacia la herramienta de origen. Por otro, introduce campos propios del sistema que serán necesarios en fases posteriores, especialmente para clasificación, remediación y verificación.

Además, al separar campos obligatorios y opcionales, el modelo resulta suficientemente flexible para trabajar con Bandit y Semgrep sin sobrediseñar la solución.

## 12. Conclusión

El modelo normalizado de hallazgos constituye una pieza central de la arquitectura del TFG. Gracias a este diseño, el sistema deja de depender directamente del formato de salida de Bandit o Semgrep y trabaja con una estructura propia, coherente con el enfoque detect–repair–verify.

La transformación de resultados de Bandit y Semgrep hacia este modelo común ya está implementada en el repositorio, junto con su enriquecimiento de clasificación (CWE/OWASP/ASVS) y su uso en salidas internas y presentables.
