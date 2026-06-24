"""CLI: ejecuta la evaluación y escribe los informes Markdown + JSON.

Uso:
    python -m app.services.evaluation [directorio_salida]

Por defecto escribe en `docs/04_delivery/`:
    - evaluation-metrics.md   (informe legible para la memoria)
    - evaluation-metrics.json (métricas en bruto)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app.services.evaluation.report import render_markdown
from app.services.evaluation.runner import _REPO_ROOT, run_evaluation

DEFAULT_OUTPUT_DIR = _REPO_ROOT / "docs" / "04_delivery"


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    output_dir = Path(args[0]) if args else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        report = run_evaluation()
    except FileNotFoundError as exc:  # corpus ausente
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    json_path = output_dir / "evaluation-metrics.json"
    md_path = output_dir / "evaluation-metrics.md"
    # Newline final para cumplir end-of-file-fixer (pre-commit) sin reescrituras.
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    md_path.write_text(render_markdown(report).rstrip("\n") + "\n", encoding="utf-8")

    s = report["summary"]
    print(
        "Evaluación completada:\n"
        f"  recall={s['recall'] * 100:.1f}%  "
        f"especificidad={s['specificity'] * 100:.1f}%  "
        f"FP={s['false_positives']}  "
        f"remediación={s['remediation_coverage'] * 100:.1f}%\n"
        f"  -> {md_path}\n"
        f"  -> {json_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
