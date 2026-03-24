from pathlib import Path

from app.services.parsers.semgrep_parser import (
    parse_semgrep_report,
    parse_semgrep_report_file,
    parse_semgrep_result,
)


def test_parse_single_semgrep_result_verify_false() -> None:
    result = {
        "check_id": "python.requests.security.disabled-cert-validation.disabled-cert-validation",
        "path": "fixtures/mvp/https_verify_false/vuln_requests_verify_false.py",
        "start": {"line": 4},
        "end": {"line": 4},
        "extra": {
            "message": "Certificate verification has been explicitly disabled.",
            "severity": "ERROR",
            "metadata": {
                "cwe": ["CWE-295: Improper Certificate Validation"],
                "source": "https://sg.run/AlYp",
            },
            "lines": 'response = requests.get("https://example.com", verify=False)',
        },
    }

    finding = parse_semgrep_result(result, analysis_target="fixtures/mvp")

    assert finding.source_tool == "semgrep"
    assert finding.source_rule_id.startswith("python.requests.security")
    assert finding.file_path.endswith("vuln_requests_verify_false.py")
    assert finding.severity == "high"
    assert finding.cwe_id == 295
    assert finding.mvp_category == "verify_false"
    assert finding.remediation_mode == "autofix_candidate"
    assert finding.candidate_for_remediation is True


def test_parse_single_semgrep_result_sql_injection() -> None:
    result = {
        "check_id": "python.lang.security.audit.formatted-sql-query.formatted-sql-query",
        "path": "fixtures/mvp/sql_injection/vuln_sql_injection.py",
        "start": {"line": 7},
        "end": {"line": 7},
        "extra": {
            "message": "Detected possible formatted SQL query. Use parameterized queries instead.",
            "severity": "WARNING",
            "metadata": {
                "cwe": ["CWE-89: SQL Injection"],
                "source": "https://sg.run/EkWw",
            },
            "lines": "return cursor.execute(query).fetchall()",
        },
    }

    finding = parse_semgrep_result(result)

    assert finding.severity == "medium"
    assert finding.cwe_id == 89
    assert finding.mvp_category == "sql_injection"
    assert finding.remediation_mode == "proposal_only"
    assert finding.candidate_for_remediation is True


def test_parse_semgrep_report_returns_list() -> None:
    report = {
        "results": [
            {
                "check_id": "python.lang.security.deserialization.avoid-pyyaml-load.avoid-pyyaml-load",
                "path": "fixtures/mvp/unsafe_yaml_load/vuln_yaml_load.py",
                "start": {"line": 4},
                "end": {"line": 4},
                "extra": {
                    "message": "Detected a possible YAML deserialization vulnerability.",
                    "severity": "ERROR",
                    "metadata": {},
                    "lines": "return yaml.load(data, Loader=yaml.Loader)",
                },
            }
        ]
    }

    findings = parse_semgrep_report(report, analysis_target="fixtures/mvp")

    assert len(findings) == 1
    assert findings[0].mvp_category == "unsafe_yaml_load"
    assert findings[0].remediation_mode == "autofix_candidate"


def test_parse_real_semgrep_report_file() -> None:
    report_path = Path("reports/semgrep/fixtures-mvp-semgrep.json")
    assert report_path.exists()

    findings = parse_semgrep_report_file(report_path)

    assert len(findings) > 0
    assert any("disabled-cert-validation" in f.source_rule_id for f in findings)
    assert any("avoid-pyyaml-load" in f.source_rule_id for f in findings)
