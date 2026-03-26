from dataclasses import dataclass

@dataclass
class RemediationProposal:
    remediation_kind: str
    applicable: bool
    confidence: str
    summary: str
    rationale: str
    original_snippet: str | None = None
    proposed_snippet: str | None = None
    changed_content: str | None = None
    verification_hint: str | None = None
