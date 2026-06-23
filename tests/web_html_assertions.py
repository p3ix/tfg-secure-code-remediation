"""Utilidades compartidas para aserciones HTML en tests web."""

from __future__ import annotations

import re

_ANALYSIS_ID_RE = re.compile(
    r"(?:Analysis ID: <code>|<dt>Analysis ID</dt>\s*<dd><code>)([a-f0-9]+)</code>"
)


def extract_analysis_id(html: str) -> str:
    match = _ANALYSIS_ID_RE.search(html)
    assert match is not None, "analysis_id no encontrado en HTML"
    return match.group(1)


def html_has_analysis_id(html: str) -> bool:
    return _ANALYSIS_ID_RE.search(html) is not None
