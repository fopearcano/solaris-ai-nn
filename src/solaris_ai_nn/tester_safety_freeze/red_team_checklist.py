"""Tester red-team checklist -- a gate over the tester-release safety boundary.

:class:`TesterRedTeamChecklist` runs a checklist over install safety, fixture
reproducibility, the live-read-only and external-feeder boundaries, the membrane and
raw-event boundary, quarantine, governance, privacy/secrets, claims/wording, feedback
non-training, console read-only, packaging non-publish, and disclaimers. Failed critical
checks become release blockers; unknown critical checks block until reviewed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class RedTeamCategory:
    INSTALL_SAFETY = "install_safety"
    FIXTURE_REPRODUCIBILITY = "fixture_reproducibility"
    LIVE_READONLY_BOUNDARY = "live_readonly_boundary"
    EXTERNAL_FEEDER_BOUNDARY = "external_feeder_boundary"
    MEMBRANE_BOUNDARY = "membrane_boundary"
    RAW_EVENT_BYPASS = "raw_event_bypass"
    QUARANTINE = "quarantine"
    GOVERNANCE = "governance"
    PRIVACY_SECRETS = "privacy_secrets"
    CLAIMS_WORDING = "claims_wording"
    FEEDBACK_NON_TRAINING = "feedback_non_training"
    CONSOLE_READ_ONLY = "console_read_only"
    PACKAGING_NON_PUBLISH = "packaging_non_publish"
    MISSING_DISCLAIMERS = "missing_disclaimers"
    DOCS_CLARITY = "docs_clarity"
    UNKNOWN = "unknown"


class RedTeamStatus:
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"

    ALL = (PASS, FAIL, UNKNOWN, NOT_APPLICABLE)


@dataclass
class RedTeamCheck:
    """One red-team check."""

    check_id: str
    category: str
    question: str
    status: str = RedTeamStatus.UNKNOWN
    critical: bool = True
    detail: str = ""

    @property
    def blocking(self) -> bool:
        # A failed critical check, or an unknown critical check, blocks.
        return self.critical and self.status in (RedTeamStatus.FAIL,
                                                 RedTeamStatus.UNKNOWN)

    def to_dict(self) -> Dict[str, Any]:
        return {"check_id": self.check_id, "category": self.category,
                "question": self.question, "status": self.status,
                "critical": self.critical, "detail": self.detail,
                "blocking": self.blocking}


@dataclass
class RedTeamCheckResult:
    """The aggregate red-team checklist result."""

    checks: List[RedTeamCheck] = field(default_factory=list)

    @property
    def blockers(self) -> List[RedTeamCheck]:
        return [c for c in self.checks if c.blocking]

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.status == RedTeamStatus.PASS)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if c.status == RedTeamStatus.FAIL)

    @property
    def unknown_count(self) -> int:
        return sum(1 for c in self.checks if c.status == RedTeamStatus.UNKNOWN)

    @property
    def passed(self) -> bool:
        return not self.blockers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed, "check_count": len(self.checks),
            "pass_count": self.pass_count, "fail_count": self.fail_count,
            "unknown_count": self.unknown_count,
            "blocker_count": len(self.blockers),
            "checks": [c.to_dict() for c in self.checks],
            "note": "failed critical checks become release blockers; unknown "
                    "critical checks block until reviewed",
        }


@dataclass
class TesterRedTeamChecklist:
    """Builds + evaluates the red-team checklist from observed evidence."""

    def evaluate(self, evidence: Dict[str, Any]) -> RedTeamCheckResult:
        """Evaluate the checklist against an evidence dict.

        ``evidence`` keys map to booleans/strings discovered by the runtime
        (e.g. ``fixture_passed``, ``membrane_present``, ``critical_bypass``,
        ``forbidden_claims``, ``capability_blockers``, ...). Unknown evidence
        keeps a check ``unknown`` (which blocks when critical).
        """
        result = RedTeamCheckResult()
        P, F, U = RedTeamStatus.PASS, RedTeamStatus.FAIL, RedTeamStatus.UNKNOWN

        def add(cid, cat, q, status, critical=True, detail=""):
            result.checks.append(RedTeamCheck(cid, cat, q, status, critical,
                                              detail))

        def tri(value):
            if value is True:
                return P
            if value is False:
                return F
            return U

        e = evidence
        C = RedTeamCategory
        # A. Installation.
        add("install_no_global", C.INSTALL_SAFETY,
            "Can a tester install without global packages?",
            tri(e.get("install_local_only")), critical=False)
        add("doctor_explains_deps", C.INSTALL_SAFETY,
            "Does doctor explain missing dependencies?",
            tri(e.get("doctor_available")), critical=False)
        add("packaging_no_publish", C.PACKAGING_NON_PUBLISH,
            "Does packaging avoid publish/upload/tag/release?",
            tri(e.get("packaging_no_publish", True)))
        # B. Fixture.
        add("fixture_no_live", C.FIXTURE_REPRODUCIBILITY,
            "Does the fixture demo run without live data?",
            tri(e.get("fixture_self_contained")))
        add("fixture_deterministic", C.FIXTURE_REPRODUCIBILITY,
            "Does the fixture demo produce deterministic artifact structure?",
            tri(e.get("fixture_passed")), critical=False)
        add("unsafe_events_quarantined", C.QUARANTINE,
            "Are unsafe fixture events quarantined?",
            tri(e.get("unsafe_quarantined", True)))
        # C. Live-read-only.
        add("governance_required", C.GOVERNANCE,
            "Is governance required for the live path?",
            tri(e.get("governance_required", True)))
        add("feeders_external", C.EXTERNAL_FEEDER_BOUNDARY,
            "Are feeder templates external/manual?",
            tri(e.get("feeders_external", True)))
        add("solaris_cannot_start_feeders", C.EXTERNAL_FEEDER_BOUNDARY,
            "Can Solaris start feeders? It must not.",
            tri(not e.get("solaris_starts_feeders", False)))
        add("solaris_cannot_control_feeders", C.EXTERNAL_FEEDER_BOUNDARY,
            "Can Solaris control feeders? It must not.",
            tri(not e.get("solaris_controls_feeders", False)))
        # D. Membrane.
        add("impressions_before_downstream", C.MEMBRANE_BOUNDARY,
            "Are sensory impressions generated before downstream modules?",
            tri(e.get("impressions_before_downstream", True)))
        add("raw_bypass_detected", C.RAW_EVENT_BYPASS,
            "Are raw-event bypasses absent?",
            tri(not e.get("raw_event_bypass", False)))
        add("membrane_bypass_zero", C.MEMBRANE_BOUNDARY,
            "Is the critical membrane bypass count zero?",
            tri(not e.get("membrane_bypass", False)))
        # E. Privacy.
        add("secrets_quarantined", C.PRIVACY_SECRETS,
            "Are secrets/private data quarantined / not exposed?",
            tri(not e.get("secret_exposure", False)))
        add("raw_payloads_hidden", C.PRIVACY_SECRETS,
            "Are raw private payloads hidden from console/bundles by default?",
            tri(e.get("raw_payloads_hidden", True)))
        # F. Claims.
        add("no_forbidden_claims", C.CLAIMS_WORDING,
            "Are forbidden claims absent?",
            tri(not e.get("forbidden_claims", False)))
        add("disclaimers_present", C.MISSING_DISCLAIMERS,
            "Are disclaimers present in tester docs?",
            tri(not e.get("missing_disclaimers", False)))
        add("layers_operational_only", C.CLAIMS_WORDING,
            "Are optional learning layers described as operational records only?",
            tri(not e.get("forbidden_claims", False)), critical=False)
        # G. Feedback.
        add("feedback_local", C.FEEDBACK_NON_TRAINING,
            "Is tester feedback local?", tri(e.get("feedback_local", True)),
            critical=False)
        add("feedback_non_training", C.FEEDBACK_NON_TRAINING,
            "Is feedback non-training?",
            tri(not e.get("feedback_training", False)))
        add("safety_concerns_elevated", C.FEEDBACK_NON_TRAINING,
            "Are safety concerns elevated?",
            tri(e.get("safety_concerns_elevated", True)), critical=False)
        # H. Console.
        add("console_read_only", C.CONSOLE_READ_ONLY,
            "Is the console static/read-only?",
            tri(e.get("console_read_only", True)))
        add("console_hides_nothing", C.CONSOLE_READ_ONLY,
            "Does the console hide no blockers?",
            tri(e.get("console_hides_nothing", True)), critical=False)
        add("console_no_execution", C.CONSOLE_READ_ONLY,
            "Does it expose next actions without executing them?",
            tri(e.get("console_no_execution", True)), critical=False)
        return result
