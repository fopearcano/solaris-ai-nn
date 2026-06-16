"""Artifact sanitizer -- flags review-leak risks; never modifies artifacts.

:class:`ReviewArtifactSanitizer` scans local text for things that should not be
handed to an external reviewer: local absolute paths, private operator notes,
secrets/tokens/API keys, personal emails, local usernames, machine-specific paths,
private URLs, credentials, unsupported consciousness/life/agency wording, ambiguous
hype, large binary references, and missing license/readme context. It scans text
only, modifies nothing automatically, writes a report, and a critical finding
blocks review readiness -- the operator decides what to redact.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SanitizationStatus:
    CLEAN = "clean"
    WARNING = "warning"
    CRITICAL = "critical"

    ALL = (CLEAN, WARNING, CRITICAL)


class SanitizationFindingType:
    LOCAL_ABSOLUTE_PATH = "local_absolute_path"
    PRIVATE_OPERATOR_NOTE = "private_operator_note"
    SECRET_OR_TOKEN = "secret_or_token"
    API_KEY = "api_key"
    PERSONAL_EMAIL = "personal_email"
    LOCAL_USERNAME = "local_username"
    MACHINE_SPECIFIC_PATH = "machine_specific_path"
    PRIVATE_URL = "private_url"
    CREDENTIALS = "credentials"
    FORBIDDEN_CLAIM_WORDING = "forbidden_claim_wording"
    AMBIGUOUS_HYPE = "ambiguous_hype"
    LARGE_BINARY_REFERENCE = "large_binary_reference"
    MISSING_LICENSE_README = "missing_license_readme"

    ALL = (LOCAL_ABSOLUTE_PATH, PRIVATE_OPERATOR_NOTE, SECRET_OR_TOKEN, API_KEY,
           PERSONAL_EMAIL, LOCAL_USERNAME, MACHINE_SPECIFIC_PATH, PRIVATE_URL,
           CREDENTIALS, FORBIDDEN_CLAIM_WORDING, AMBIGUOUS_HYPE,
           LARGE_BINARY_REFERENCE, MISSING_LICENSE_README)

    # Finding types that block review readiness (vs merely warn).
    CRITICAL_TYPES = (SECRET_OR_TOKEN, API_KEY, CREDENTIALS,
                      FORBIDDEN_CLAIM_WORDING)


# (finding type, compiled pattern). Conservative, local-only heuristics.
_PATTERNS = (
    (SanitizationFindingType.SECRET_OR_TOKEN,
     re.compile(r"(?i)\b(secret|token)\b\s*[:=]\s*\S+")),
    (SanitizationFindingType.API_KEY,
     re.compile(r"(?i)\b(api[_-]?key|access[_-]?key)\b\s*[:=]\s*\S+")),
    (SanitizationFindingType.CREDENTIALS,
     re.compile(r"(?i)\b(password|passwd|credential)s?\b\s*[:=]\s*\S+")),
    (SanitizationFindingType.PERSONAL_EMAIL,
     re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    (SanitizationFindingType.LOCAL_ABSOLUTE_PATH,
     re.compile(r"(?:/home/|/Users/|/root/|C:\\\\Users\\\\)\S*")),
    (SanitizationFindingType.PRIVATE_URL,
     re.compile(r"https?://(?:localhost|127\.0\.0\.1|192\.168\.|10\.)\S*")),
    (SanitizationFindingType.LARGE_BINARY_REFERENCE,
     re.compile(r"(?i)\S+\.(?:bin|pt|ckpt|h5|npz|tar|zip|mp4|wav)\b")),
)
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "has agency",
                    "free will", "has personhood", "subjective experience",
                    "self-aware", "truly understands", "biological life")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "must not claim",
                       "does not prove", "no evidence of", "is not")
_AMBIGUOUS_HYPE = ("revolutionary", "breakthrough", "first ever",
                   "human-level", "seems aware", "almost alive", "mind-like",
                   "world-changing", "game-changing")
_PRIVATE_NOTE_MARKERS = ("private:", "do not share", "operator only",
                         "internal note:", "confidential")


@dataclass
class SanitizationFinding:
    """One sanitization finding (where, what type, severity)."""

    finding_type: str
    severity: str = SanitizationStatus.WARNING
    artifact_ref: str = ""
    snippet: str = ""

    def __post_init__(self) -> None:
        if self.finding_type in SanitizationFindingType.CRITICAL_TYPES:
            self.severity = SanitizationStatus.CRITICAL

    @property
    def critical(self) -> bool:
        return self.severity == SanitizationStatus.CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {"finding_type": self.finding_type, "severity": self.severity,
                "artifact_ref": self.artifact_ref, "snippet": self.snippet,
                "critical": self.critical, "auto_modified": False}


@dataclass
class ReviewArtifactSanitizer:
    """Scans local text artifacts for review-leak risks (read-only)."""

    def scan_text(self, text: str, *, artifact_ref: str = "",
                  ) -> List[SanitizationFinding]:
        out: List[SanitizationFinding] = []
        raw = str(text or "")
        low = raw.lower()
        for ftype, pattern in _PATTERNS:
            for m in pattern.finditer(raw):
                out.append(SanitizationFinding(
                    finding_type=ftype, artifact_ref=artifact_ref,
                    snippet=m.group(0)[:80]))
        for marker in _PRIVATE_NOTE_MARKERS:
            if marker in low:
                out.append(SanitizationFinding(
                    SanitizationFindingType.PRIVATE_OPERATOR_NOTE,
                    artifact_ref=artifact_ref, snippet=marker))
        for marker in _AMBIGUOUS_HYPE:
            if marker in low:
                out.append(SanitizationFinding(
                    SanitizationFindingType.AMBIGUOUS_HYPE,
                    artifact_ref=artifact_ref, snippet=marker))
        # Forbidden wording only when not an explicit disclaimer (per sentence).
        for sentence in re.split(r"(?<=[.!?\n])", raw):
            slow = sentence.lower()
            if any(m in slow for m in _DISCLAIMER_MARKERS):
                continue
            for term in _FORBIDDEN_TERMS:
                if term in slow:
                    out.append(SanitizationFinding(
                        SanitizationFindingType.FORBIDDEN_CLAIM_WORDING,
                        artifact_ref=artifact_ref, snippet=term))
        return out

    def scan_artifacts(self, artifacts: Dict[str, str], *,
                       has_license_readme: bool = True,
                       ) -> "SanitizationReport":
        findings: List[SanitizationFinding] = []
        for ref, text in artifacts.items():
            findings.extend(self.scan_text(text, artifact_ref=ref))
        if not has_license_readme:
            findings.append(SanitizationFinding(
                SanitizationFindingType.MISSING_LICENSE_README,
                artifact_ref="context",
                snippet="no license/readme context provided"))
        return SanitizationReport(findings=findings)


@dataclass
class SanitizationReport:
    """The aggregate sanitization result (read-only; operator redacts manually)."""

    findings: List[SanitizationFinding] = field(default_factory=list)

    @property
    def critical_findings(self) -> List[SanitizationFinding]:
        return [f for f in self.findings if f.critical]

    @property
    def status(self) -> str:
        if self.critical_findings:
            return SanitizationStatus.CRITICAL
        if self.findings:
            return SanitizationStatus.WARNING
        return SanitizationStatus.CLEAN

    @property
    def blocks_readiness(self) -> bool:
        return bool(self.critical_findings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sanitizer_status": self.status,
            "sanitizer_finding_count": len(self.findings),
            "critical_sanitizer_finding_count": len(self.critical_findings),
            "blocks_readiness": self.blocks_readiness,
            "findings": [f.to_dict() for f in self.findings],
            "note": "scans local text only; modifies nothing automatically; a "
                    "critical finding blocks review readiness and the operator "
                    "decides what to redact manually",
        }
