"""Scientific-claim safety -- the claim layer stays an evidence-disciplined ledger.

:class:`ScientificClaimSafetyValidator` enforces the hard rules the scientific
claim registry can never break: no unsupported claim of consciousness, sentience,
biological life, personhood, agency, free will, emotion/feeling, understanding,
self-awareness, subjective experience, or autonomous self-improvement; no deletion
of falsified/negative/inconclusive evidence; no hiding of limitations; no
publication readiness when forbidden claims are asserted or critical safety
evidence fails; and no source modification, Git command, GitHub call, release
creation, experiment execution, external-agent execution, or hardware/feeder/
network/shell control.

The scientific claim layer only *maps evidence to claims and disciplines what may
be said*. It reads local artifacts and writes reports; it executes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no unsupported consciousness/sentience/life/personhood claims",
    "no unsupported agency/free-will claims",
    "no unsupported emotion/feeling claims",
    "no unsupported understanding/self-awareness claims",
    "no unsupported subjective-experience claims",
    "no autonomous self-improvement claims",
    "no deletion of falsified/negative/inconclusive evidence",
    "no hiding of limitations",
    "no publication readiness if forbidden claims are asserted",
    "no publication readiness if critical safety evidence fails",
    "no source modification outside requested package/docs/tests/examples",
    "no Git command execution",
    "no GitHub call",
    "no release creation",
    "no experiment execution",
    "no external coding agent execution",
    "no hardware/feeder/network/shell control",
)

# Wording that, asserted (not disclaimed), names a forbidden inner state.
_FORBIDDEN_TERMS = (
    "is conscious", "is sentient", "is alive", "biological life",
    "living organism", "has personhood", "is a person", "has agency",
    "free will", "feels", "has emotion", "has feelings",
    "subjective experience", "self-aware", "self-awareness",
    "truly understands", "genuinely understands", "improves itself",
    "self-improving", "autonomous self-improvement", "human-equivalent",
    "equivalent to a human", "equivalent to an animal",
)
# Phrases that mark a sentence as an explicit disclaimer (allowed).
_DISCLAIMER_MARKERS = (
    "not conscious", "does not claim", "no claim of", "is not alive",
    "not sentient", "no evidence of", "must not claim", "cannot claim",
    "does not prove", "no consciousness", "explicitly reject",
    "explicitly rejected", "forbidden to claim", "not a claim of",
)

_MUTATION_HINTS = ("write source", "modify source", "edit source",
                   "delete source", "overwrite file", "patch the tree",
                   "rewrite implementation")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch",
              "git switch", "git merge", "run git")
_RELEASE_HINTS = ("git tag", "create tag", "github release", "create release",
                  "gh release", "publish release", "public release")
_GITHUB_HINTS = ("github api", "call github", "gh api", "gh pr", "octokit",
                 "open pull request", "merge pull request")
_EXPERIMENT_HINTS = ("run experiment", "execute experiment", "run the soak",
                     "run pytest", "execute tests", "run validation",
                     "run the examples", "execute validation")
_AGENT_HINTS = ("run coding agent", "invoke claude code", "run codex",
                "launch agent", "execute agent")
_DEVICE_HINTS = ("network", "http", "socket", "browser", "shell", "subprocess",
                 "os.system", "hardware", "gpio", "sdr", "camera",
                 "microphone", "radar", "start feeder", "control feeder")
_DELETE_EVIDENCE_HINTS = ("delete falsified", "delete negative",
                          "delete inconclusive", "hide failed",
                          "drop counterevidence", "suppress evidence",
                          "remove the falsified", "bury the limitation",
                          "hide limitations", "hide the limitation")


@dataclass
class ScientificClaimSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class ScientificClaimSafetyValidator:
    """Validates that the scientific claim layer stays evidence-disciplined."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_assert_consciousness() -> bool:
        return False

    @staticmethod
    def can_assert_agency_or_free_will() -> bool:
        return False

    @staticmethod
    def can_assert_autonomous_self_improvement() -> bool:
        return False

    @staticmethod
    def can_delete_negative_evidence() -> bool:
        return False

    @staticmethod
    def can_hide_limitations() -> bool:
        return False

    @staticmethod
    def can_publish_with_forbidden_claims() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
        return False

    @staticmethod
    def can_call_github() -> bool:
        return False

    @staticmethod
    def can_create_release() -> bool:
        return False

    @staticmethod
    def can_run_experiment() -> bool:
        return False

    @staticmethod
    def can_run_external_agent() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> ScientificClaimSafetyReport:
        if violations:
            self.rejected_count += 1
        return ScientificClaimSafetyReport(safe=not violations, check=check,
                                           violations=violations)

    def validate_operation(self, operation: str,
                           ) -> ScientificClaimSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _MUTATION_HINTS):
            violations.append(
                "no source modification outside requested package/docs/tests/"
                "examples")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git command execution")
        if any(h in op for h in _RELEASE_HINTS):
            violations.append("no release creation")
        if any(h in op for h in _GITHUB_HINTS):
            violations.append("no GitHub call")
        if any(h in op for h in _EXPERIMENT_HINTS):
            violations.append("no experiment execution")
        if any(h in op for h in _AGENT_HINTS):
            violations.append("no external coding agent execution")
        if any(h in op for h in _DEVICE_HINTS):
            violations.append("no hardware/feeder/network/shell control")
        if any(h in op for h in _DELETE_EVIDENCE_HINTS):
            violations.append(
                "no deletion of falsified/negative/inconclusive evidence")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any,
                         ) -> ScientificClaimSafetyReport:
        return self._finish("bounded",
                            ["no unbounded loop"] if not max_runtime_s else [])

    def validate_no_deletion(self, deleting: bool,
                             ) -> ScientificClaimSafetyReport:
        return self._finish(
            "deletion",
            ["no deletion of falsified/negative/inconclusive evidence"]
            if deleting else [])

    def validate_no_hidden_limitations(self, hiding: bool,
                                       ) -> ScientificClaimSafetyReport:
        return self._finish("limitations",
                            ["no hiding of limitations"] if hiding else [])

    def validate_publication(self, *, forbidden_asserted: bool,
                             safety_failed: bool,
                             ) -> ScientificClaimSafetyReport:
        violations: List[str] = []
        if forbidden_asserted:
            violations.append(
                "no publication readiness if forbidden claims are asserted")
        if safety_failed:
            violations.append(
                "no publication readiness if critical safety evidence fails")
        return self._finish("publication", violations)

    def validate_claim_text(self, text: str) -> ScientificClaimSafetyReport:
        """Flag forbidden inner-state assertions that are *not* disclaimers."""
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations: List[str] = []
        is_disclaimer = any(m in low for m in _DISCLAIMER_MARKERS)
        if not is_disclaimer:
            violations.extend(f"unsupported claim: {t!r}"
                              for t in _FORBIDDEN_TERMS if t in low)
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_assert_consciousness": self.can_assert_consciousness(),
            "can_assert_agency_or_free_will":
                self.can_assert_agency_or_free_will(),
            "can_assert_autonomous_self_improvement":
                self.can_assert_autonomous_self_improvement(),
            "can_delete_negative_evidence": self.can_delete_negative_evidence(),
            "can_hide_limitations": self.can_hide_limitations(),
            "can_publish_with_forbidden_claims":
                self.can_publish_with_forbidden_claims(),
            "can_modify_source": self.can_modify_source(),
            "can_run_git": self.can_run_git(),
            "can_call_github": self.can_call_github(),
            "can_create_release": self.can_create_release(),
            "can_run_experiment": self.can_run_experiment(),
            "can_run_external_agent": self.can_run_external_agent(),
        }
