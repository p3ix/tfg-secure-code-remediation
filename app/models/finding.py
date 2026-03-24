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
