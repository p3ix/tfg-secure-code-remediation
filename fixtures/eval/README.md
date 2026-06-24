# Corpus de evaluación cuantitativa

Extiende `fixtures/mvp/` (solo-vulnerable) con un control **limpio** para poder
medir no solo *recall* sino también **falsos positivos / especificidad**.

- `ground_truth.json` — etiquetas: casos `vulnerable` (categoría MVP + CWE + si se
  espera autofix) y casos `clean` (variante segura que **no** debe disparar la
  categoría indicada).
- `clean/` — variantes corregidas mínimas (una por categoría con remediación).

## Cómo ejecutar la evaluación

```bash
python -m app.services.evaluation
```

Requiere Bandit y Semgrep en el `PATH` (escanea el corpus real). Genera:

- `docs/04_delivery/evaluation-metrics.md` — informe legible para la memoria.
- `docs/04_delivery/evaluation-metrics.json` — métricas en bruto.

Las funciones de cálculo de métricas son deterministas y están cubiertas por
`tests/test_evaluation_metrics.py` (sin depender de las herramientas externas).
