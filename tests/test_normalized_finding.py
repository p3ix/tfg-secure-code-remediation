from dataclasses import asdict

from app.models.finding import NormalizedFinding


def test_can_create_bandit_normalized_finding() -> None:
    finding = NormalizedFinding(
        source_tool="bandit",
        source_rule_id="B501",
        source_rule_name="request_with_no_cert_validation",
        file_path="fixtures/mvp/https_verify_false/vuln_requests_verify_false.py",
        line_start=4,
        line_end=4,
        code_snippet='response = requests.get("https://example.com", verify=False)',
        title="Desactivación de verificación TLS",
        description="Se ha detectado una petición HTTPS con verify=False.",
        severity="high",
        confidence="high",
        raw_message="Call to requests with verify=False disabling SSL certificate checks, security issue.",
        reference_url="https://bandit.readthedocs.io/en/1.9.4/plugins/b501_request_with_no_cert_validation.html",
        cwe_id=295,
        cwe_url="https://cwe.mitre.org/data/definitions/295.html",
        owasp_top10=None,
        owasp_asvs=None,
        mvp_category="verify_false",
        candidate_for_remediation=True,
        remediation_mode="autofix_candidate",
        verification_status="pending",
        detected_at=None,
        analysis_target="fixtures/mvp",
        raw_tool_data={},
    )

    assert finding.source_tool == "bandit"
    assert finding.source_rule_id == "B501"
    assert finding.severity == "high"
    assert finding.mvp_category == "verify_false"
    assert finding.candidate_for_remediation is True
    assert finding.remediation_mode == "autofix_candidate"


def test_can_create_semgrep_normalized_finding() -> None:
    finding = NormalizedFinding(
        source_tool="semgrep",
        source_rule_id="python.lang.security.deserialization.avoid-pyyaml-load.avoid-pyyaml-load",
        source_rule_name=None,
        file_path="fixtures/mvp/unsafe_yaml_load/vuln_yaml_load.py",
        line_start=4,
        line_end=4,
        code_snippet="return yaml.load(data, Loader=yaml.Loader)",
        title="Uso inseguro de yaml.load",
        description="Se ha detectado una posible deserialización YAML insegura.",
        severity="high",
        confidence="unknown",
        raw_message="Detected a possible YAML deserialization vulnerability.",
        reference_url="https://sg.run/we9Y",
        cwe_id=None,
        cwe_url=None,
        owasp_top10=None,
        owasp_asvs=None,
        mvp_category="unsafe_yaml_load",
        candidate_for_remediation=True,
        remediation_mode="autofix_candidate",
        verification_status="pending",
        detected_at=None,
        analysis_target="fixtures/mvp",
        raw_tool_data={},
    )

    finding_dict = asdict(finding)

    assert finding.source_tool == "semgrep"
    assert finding.file_path.endswith("vuln_yaml_load.py")
    assert finding.remediation_mode == "autofix_candidate"
    assert finding_dict["source_rule_id"].startswith("python.lang.security")
    assert finding_dict["candidate_for_remediation"] is True


def test_optional_fields_can_be_none() -> None:
    finding = NormalizedFinding(
        source_tool="bandit",
        source_rule_id="B602",
        file_path="fixtures/mvp/command_injection/vuln_shell_true.py",
        line_start=4,
        raw_message="subprocess call with shell=True identified, security issue.",
        severity="high",
        mvp_category="command_injection",
        candidate_for_remediation=True,
        remediation_mode="autofix_candidate",
    )

    assert finding.source_rule_name is None
    assert finding.line_end is None
    assert finding.reference_url is None
    assert finding.raw_tool_data is None
