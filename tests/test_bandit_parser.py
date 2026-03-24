import json
from pathlib import Path

from app.services.parsers.bandit_parser import (
    parse_bandit_report,
    parse_bandit_report_file,
    parse_bandit_result,
)


def test_parse_single_bandit_result_verify_false() -> None:
    result = {
        "filename": "fixtures/mvp/https_verify_false/vuln_requests_verify_false.py",
        "test_id": "B501",
        "test_name": "request_with_no_cert_validation",
        "issue_severity": "HIGH",
        "issue_confidence": "HIGH",
        "issue_text": "Call to requests with verify=False disabling SSL certificate checks, security issue.",
        "line_number": 4,
        "line_range": [4],
        "code": 'response = requests.get("https://example.com", verify=False)',
        "more_info": "https://bandit.readthedocs.io/en/1.9.4/plugins/b501_request_with_no_cert_validation.html",
        "issue_cwe": {
            "id": 295,
            "link": "https://cwe.mitre.org/data/definitions/295.html",
        },
    }

    finding = parse_bandit_result(result, analysis_target="fixtures/mvp")

    assert finding.source_tool == "bandit"
    assert finding.source_rule_id == "B501"
    assert finding.file_path.endswith("vuln_requests_verify_false.py")
    assert finding.severity == "high"
    assert finding.confidence == "high"
    assert finding.cwe_id == 295
    assert finding.mvp_category == "verify_false"
    assert finding.remediation_mode == "autofix_candidate"
    assert finding.candidate_for_remediation is True


def test_parse_single_bandit_result_sql_injection() -> None:
    result = {
        "filename": "fixtures/mvp/sql_injection/vuln_sql_injection.py",
        "test_id": "B608",
        "test_name": "hardcoded_sql_expressions",
        "issue_severity": "MEDIUM",
        "issue_confidence": "LOW",
        "issue_text": "Possible SQL injection vector through string-based query construction.",
        "line_number": 6,
        "line_range": [6],
        "code": 'query = f"SELECT * FROM users WHERE username = \'{username}\'"',
        "more_info": "https://bandit.readthedocs.io/en/1.9.4/plugins/b608_hardcoded_sql_expressions.html",
        "issue_cwe": {
            "id": 89,
            "link": "https://cwe.mitre.org/data/definitions/89.html",
        },
    }

    finding = parse_bandit_result(result)

    assert finding.source_rule_id == "B608"
    assert finding.severity == "medium"
    assert finding.confidence == "low"
    assert finding.mvp_category == "sql_injection"
    assert finding.remediation_mode == "proposal_only"
    assert finding.candidate_for_remediation is True


def test_parse_bandit_report_returns_list() -> None:
    report = {
        "results": [
            {
                "filename": "fixtures/mvp/unsafe_yaml_load/vuln_yaml_load.py",
                "test_id": "B506",
                "test_name": "yaml_load",
                "issue_severity": "MEDIUM",
                "issue_confidence": "HIGH",
                "issue_text": "Use of unsafe yaml load.",
                "line_number": 4,
                "line_range": [4],
                "code": "return yaml.load(data, Loader=yaml.Loader)",
                "more_info": "https://bandit.readthedocs.io/",
                "issue_cwe": {
                    "id": 20,
                    "link": "https://cwe.mitre.org/data/definitions/20.html",
                },
            }
        ]
    }

    findings = parse_bandit_report(report, analysis_target="fixtures/mvp")

    assert len(findings) == 1
    assert findings[0].mvp_category == "unsafe_yaml_load"
    assert findings[0].remediation_mode == "autofix_candidate"


def test_parse_real_bandit_report_file() -> None:
    report_path = Path("reports/bandit/fixtures-mvp-bandit.json")
    assert report_path.exists()

    findings = parse_bandit_report_file(report_path)

    assert len(findings) > 0
    assert any(f.source_rule_id == "B501" for f in findings)
    assert any(f.source_rule_id == "B506" for f in findings)
