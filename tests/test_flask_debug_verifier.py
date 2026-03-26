from pathlib import Path

from app.services.verification.flask_debug_verifier import (
    verify_flask_debug_remediation,
)


def test_verify_flask_debug_remediation_succeeds_on_real_fixture() -> None:
    fixture_path = Path("fixtures/mvp/flask_debug_true/vuln_flask_debug_true.py")
    source_code = fixture_path.read_text(encoding="utf-8")

    result = verify_flask_debug_remediation(source_code)

    assert result["applicable"] is True
    assert result["verified"] is True
    assert result["remaining_findings"] == []
    assert result["proposed_snippet"] == "debug=False"


def test_verify_flask_debug_remediation_not_applicable_on_safe_code() -> None:
    source_code = """
from flask import Flask

app = Flask(__name__)

if __name__ == "__main__":
    app.run(debug=False)
""".strip()

    result = verify_flask_debug_remediation(source_code)

    assert result["applicable"] is False
    assert result["verified"] is False
