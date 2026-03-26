from pathlib import Path

from app.services.remediations.flask_debug_remediator import (
    propose_flask_debug_remediation,
)


def test_flask_debug_remediation_replaces_simple_pattern() -> None:
    source_code = """
from flask import Flask

app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=True)
""".strip()

    proposal = propose_flask_debug_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.confidence == "high"
    assert proposal.original_snippet == "debug=True"
    assert proposal.proposed_snippet == "debug=False"
    assert proposal.changed_content is not None
    assert "debug=False" in proposal.changed_content
    assert "debug=True" not in proposal.changed_content


def test_flask_debug_remediation_returns_not_applicable_when_pattern_absent() -> None:
    source_code = """
from flask import Flask

app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=False)
""".strip()

    proposal = propose_flask_debug_remediation(source_code)

    assert proposal.applicable is False
    assert proposal.changed_content is None


def test_flask_debug_remediation_works_with_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/flask_debug_true/vuln_flask_debug_true.py")
    assert fixture_path.exists()

    source_code = fixture_path.read_text(encoding="utf-8")
    proposal = propose_flask_debug_remediation(source_code)

    assert proposal.applicable is True
    assert proposal.changed_content is not None
    assert "debug=False" in proposal.changed_content
    assert "debug=True" not in proposal.changed_content
