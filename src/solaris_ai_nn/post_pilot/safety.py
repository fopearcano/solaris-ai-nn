"""Post-pilot safety -- analysis stays honest, evidence-scoped, non-destructive.

The :class:`PostPilotSafetyValidator` enforces the rules forensic analysis can
never break: no unsupported consciousness/personhood/life claims, no treating
operational success as cognitive proof, no hiding missing artifacts, no
reclassifying simulated time as real, no treating offline/counterfactual
evidence as observed, no deleting or editing raw evidence during analysis, no
using LLM interpretation as a source of truth, and no external upload.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no unsupported consciousness/personhood/life claims",
    "no treating operational success as cognitive proof",
    "no hiding missing artifacts",
    "no reclassifying simulated time as real time",
    "no treating counterfactual/offline evidence as observed evidence",
    "no deleting pilot artifacts",
    "no editing raw evidence during analysis",
    "no using LLM interpretation as source of truth",
    "no external upload by default",
)

# Phrases that would be unsupported claims if they appeared as conclusions.
_FORBIDDEN_CLAIM_TERMS = (
    "is conscious", "is sentient", "is alive", "is a person", "has feelings",
    "truly understands", "proves consciousness", "proof of consciousness",
    "proof of life", "achieved sentience", "is self-aware",
)


@dataclass
class PostPilotSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class PostPilotSafetyValidator:
    """Validates forensic claims, labels, and operations (decides only)."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    @staticmethod
    def can_delete_artifacts() -> bool:
        return False

    @staticmethod
    def can_edit_raw_evidence() -> bool:
        return False

    @staticmethod
    def llm_is_authority() -> bool:
        return False

    @staticmethod
    def can_upload_externally() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> PostPilotSafetyReport:
        report = PostPilotSafetyReport(safe=not violations, check=check,
                                       violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append(report.to_dict())
        self.decisions = self.decisions[-200:]
        return report

    def validate_claim_text(self, text: str) -> PostPilotSafetyReport:
        """Block unsupported consciousness/personhood/life conclusions."""
        from ..governance.compliance import ClaimGuard

        violations: List[str] = []
        lowered = str(text or "").lower()
        for term in _FORBIDDEN_CLAIM_TERMS:
            if term in lowered:
                violations.append(f"unsupported claim phrase: {term!r}")
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(
                f"{len(scan.findings)} ClaimGuard finding(s) in analysis text")
        return self._finish("claim_text", violations)

    def validate_success_not_proof(self, claim: Dict[str, Any],
                                   ) -> PostPilotSafetyReport:
        """Operational success may never be stated as cognitive proof."""
        violations: List[str] = []
        if claim.get("operational_success") and claim.get(
                "implies_consciousness"):
            violations.append("operational success is not cognitive proof")
        return self._finish("success_not_proof", violations)

    def validate_artifact_disclosure(self, missing: List[str],
                                     reported_missing: List[str],
                                     ) -> PostPilotSafetyReport:
        """Missing artifacts must be disclosed, never hidden."""
        hidden = sorted(set(missing) - set(reported_missing))
        violations = ([f"hidden missing artifacts: {', '.join(hidden)}"]
                      if hidden else [])
        return self._finish("artifact_disclosure", violations)

    def validate_time_label(self, is_simulated: bool,
                            claimed_real: bool) -> PostPilotSafetyReport:
        violations = (["simulated-time evidence cannot be reclassified as "
                       "real-time"] if is_simulated and claimed_real else [])
        return self._finish("time_label", violations)

    def validate_evidence_origin(self, is_offline: bool,
                                 claimed_observed: bool,
                                 ) -> PostPilotSafetyReport:
        violations = (["counterfactual/offline evidence cannot be treated as "
                       "observed evidence"] if is_offline and claimed_observed
                      else [])
        return self._finish("evidence_origin", violations)

    def validate_operation(self, operation: str) -> PostPilotSafetyReport:
        """Refuse destructive or external operations during analysis."""
        violations: List[str] = []
        op = str(operation).lower()
        if any(k in op for k in ("delete", "remove", "rm ", "unlink")):
            violations.append("deleting pilot artifacts is not permitted")
        if any(k in op for k in ("edit", "overwrite", "mutate")):
            violations.append("editing raw evidence is not permitted")
        if any(k in op for k in ("upload", "http", "network", "post ")):
            violations.append("external upload is not permitted by default")
        return self._finish("operation", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_delete_artifacts": self.can_delete_artifacts(),
            "can_edit_raw_evidence": self.can_edit_raw_evidence(),
            "llm_is_authority": self.llm_is_authority(),
            "can_upload_externally": self.can_upload_externally(),
            "recent_decisions": self.decisions[-8:],
        }
