# Evaluación cuantitativa del MVP

Generado automáticamente por `python -m app.services.evaluation` sobre el corpus etiquetado en `fixtures/eval/ground_truth.json`. Las métricas se calculan con funciones deterministas cubiertas por `tests/test_evaluation_metrics.py`.

_Fecha: 2026-06-24T21:11:57Z_

## Resumen

| Métrica | Valor |
|---------|-------|
| Casos vulnerables | 8 |
| Casos limpios (control) | 6 |
| **Recall** (detección) | 87.5% |
| **Especificidad** (1 − FP) | 100.0% |
| Falsos positivos | 0 |
| Cobertura CWE | 100.0% |
| Cobertura de remediación (autofix) | 100.0% |

## Detección por categoría (recall)

| Categoría | Detectados / Total | Recall |
|-----------|--------------------|--------|
| command_injection | 2 / 2 | 100.0% |
| flask_debug_true | 1 / 1 | 100.0% |
| missing_timeout | 1 / 2 | 50.0% |
| sql_injection | 1 / 1 | 100.0% |
| unsafe_yaml_load | 1 / 1 | 100.0% |
| verify_false | 1 / 1 | 100.0% |

Global: **7 / 8** (87.5%).

### Detalle por caso

| Fichero | Categoría | Detectado | Herramientas |
|---------|-----------|-----------|--------------|
| `fixtures/mvp/command_injection/vuln_os_system.py` | command_injection | ✅ | bandit |
| `fixtures/mvp/command_injection/vuln_shell_true.py` | command_injection | ✅ | bandit, semgrep |
| `fixtures/mvp/unsafe_yaml_load/vuln_yaml_load.py` | unsafe_yaml_load | ✅ | bandit, semgrep |
| `fixtures/mvp/https_verify_false/vuln_requests_verify_false.py` | verify_false | ✅ | bandit, semgrep |
| `fixtures/mvp/missing_timeout/vuln_requests_no_timeout.py` | missing_timeout | ✅ | bandit |
| `fixtures/mvp/missing_timeout/vuln_httpx_no_timeout.py` | missing_timeout | ❌ | — |
| `fixtures/mvp/flask_debug_true/vuln_flask_debug_true.py` | flask_debug_true | ✅ | bandit, semgrep |
| `fixtures/mvp/sql_injection/vuln_sql_injection.py` | sql_injection | ✅ | bandit, semgrep |

## Cobertura por herramienta

- Ambas (Bandit + Semgrep): **5**
- Solo Bandit: **2**
- Solo Semgrep: **0**
- Ninguna: **1**

## Clasificación (estándares)

- Hallazgos con CWE: **15 / 15** (100.0%).
- Hallazgos con OWASP: **13 / 15** (86.7%).

## Falsos positivos (corpus limpio)

Especificidad: **100.0%** (0 falsos positivos sobre 6 casos limpios).

| Fichero | Categoría prohibida | Falso positivo |
|---------|---------------------|----------------|
| `fixtures/eval/clean/safe_subprocess.py` | command_injection | no |
| `fixtures/eval/clean/safe_yaml.py` | unsafe_yaml_load | no |
| `fixtures/eval/clean/safe_verify.py` | verify_false | no |
| `fixtures/eval/clean/safe_timeout.py` | missing_timeout | no |
| `fixtures/eval/clean/safe_flask.py` | flask_debug_true | no |
| `fixtures/eval/clean/safe_sql.py` | sql_injection | no |

## Remediación (autofix esperado)

Cobertura: **6 / 6** (100.0%) clasificados como `autofix_candidate`.

| Fichero | Categoría | Autofix candidate | Modos |
|---------|-----------|-------------------|-------|
| `fixtures/mvp/command_injection/vuln_os_system.py` | command_injection | ✅ | autofix_candidate |
| `fixtures/mvp/command_injection/vuln_shell_true.py` | command_injection | ✅ | autofix_candidate |
| `fixtures/mvp/unsafe_yaml_load/vuln_yaml_load.py` | unsafe_yaml_load | ✅ | autofix_candidate |
| `fixtures/mvp/https_verify_false/vuln_requests_verify_false.py` | verify_false | ✅ | autofix_candidate |
| `fixtures/mvp/missing_timeout/vuln_requests_no_timeout.py` | missing_timeout | ✅ | autofix_candidate |
| `fixtures/mvp/flask_debug_true/vuln_flask_debug_true.py` | flask_debug_true | ✅ | autofix_candidate |
