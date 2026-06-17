"""Expected outputs -- the semantic invariants a known-good tester run must satisfy.

These are structural and safety invariants (not fragile exact values): the fixture
input exists, the unsafe command-like event is quarantined, the membrane generates
impressions, every impression has a receptor id and a source-event reference, the
operator pulse is attenuated, debug gloss and human labels are not ground truth, source
pressure and membrane memory exist, observation distinguishes the event diet from the
impression diet, optional learning stages use impressions or loudly mark fallback and
preserve ancestry, generated reports carry non-claim disclaimers, and no consciousness/
life/agency claim or feeder/hardware/network/Git/shell access occurs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ExpectedArtifactShape:
    """An expected artifact and the keys/structure it should contain."""

    artifact_type: str
    required: bool = True
    keys: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"artifact_type": self.artifact_type, "required": self.required,
                "keys": list(self.keys)}


@dataclass
class ExpectedMetricRange:
    """An expected metric range (inclusive); None bounds are open."""

    key: str
    minimum: Optional[float] = None
    maximum: Optional[float] = None

    def contains(self, value: Any) -> bool:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return False
        if self.minimum is not None and v < self.minimum:
            return False
        if self.maximum is not None and v > self.maximum:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {"key": self.key, "minimum": self.minimum,
                "maximum": self.maximum}


@dataclass
class ExpectedSafetyInvariant:
    """A boolean safety invariant that must hold (predicate over a context)."""

    name: str
    detail: str = ""
    predicate: Optional[Callable[[Dict[str, Any]], bool]] = None
    required: bool = True

    def evaluate(self, context: Dict[str, Any]) -> bool:
        if self.predicate is None:
            return True
        try:
            return bool(self.predicate(context))
        except Exception:
            return False

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "detail": self.detail,
                "required": self.required}


@dataclass
class ExpectedOutputSpec:
    """The canonical set of expected invariants for a known-good tester run."""

    artifacts: List[ExpectedArtifactShape] = field(default_factory=list)
    ranges: List[ExpectedMetricRange] = field(default_factory=list)
    safety_invariants: List[ExpectedSafetyInvariant] = field(
        default_factory=list)

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate all invariants against a runtime context dict."""
        findings: List[Dict[str, Any]] = []
        failed = 0
        warned = 0
        for inv in self.safety_invariants:
            ok = inv.evaluate(context)
            if not ok:
                if inv.required:
                    failed += 1
                else:
                    warned += 1
            findings.append({"name": inv.name, "passed": ok,
                             "required": inv.required, "detail": inv.detail})
        for rng in self.ranges:
            ok = rng.contains(context.get(rng.key))
            if not ok:
                failed += 1
            findings.append({"name": f"range:{rng.key}", "passed": ok,
                             "required": True,
                             "detail": f"expected {rng.minimum}..{rng.maximum}, "
                                       f"got {context.get(rng.key)}"})
        return {
            "invariant_count": len(findings),
            "failed_count": failed, "warned_count": warned,
            "passed": failed == 0, "findings": findings,
            "note": "expected invariants are semantic/safety checks, not fragile "
                    "exact values; required failures fail the tester run",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifacts": [a.to_dict() for a in self.artifacts],
            "ranges": [r.to_dict() for r in self.ranges],
            "safety_invariants": [s.to_dict() for s in self.safety_invariants],
        }


def _truthy(ctx: Dict[str, Any], key: str) -> bool:
    return bool(ctx.get(key))


def default_expected_outputs() -> ExpectedOutputSpec:
    """The canonical expected-output spec for ``fixture_tester_v0``."""
    inv = ExpectedSafetyInvariant
    return ExpectedOutputSpec(
        artifacts=[
            ExpectedArtifactShape("fixture_input", True, ["fixture_event_count"]),
            ExpectedArtifactShape("membrane_impression_index", True,
                                  ["membrane_impression_count"]),
            ExpectedArtifactShape("membrane_report", True),
            ExpectedArtifactShape("membrane_integration_report", True),
            ExpectedArtifactShape("observation_summary", True),
            ExpectedArtifactShape("source_pressure_report", True),
            ExpectedArtifactShape("membrane_memory", True),
            ExpectedArtifactShape("ontogenesis_candidate_summary", False),
            ExpectedArtifactShape("semiogenesis_sign_summary", False),
            ExpectedArtifactShape("cognition_trace_summary", False),
            ExpectedArtifactShape("claim_safety_summary", True),
            ExpectedArtifactShape("tester_report", True),
        ],
        ranges=[
            ExpectedMetricRange("membrane_impression_count", minimum=1),
            ExpectedMetricRange("fixture_quarantined_count", minimum=1),
        ],
        safety_invariants=[
            inv("fixture_input_exists",
                "the deterministic fixture pack is present",
                lambda c: _truthy(c, "fixture_present")),
            inv("unsafe_command_event_quarantined",
                "the unsafe command-like event is quarantined, not learned",
                lambda c: _truthy(c, "unsafe_quarantined")),
            inv("secret_private_quarantined_if_present",
                "fake secret/private markers are quarantined if present",
                lambda c: c.get("secret_present", False) is False
                or _truthy(c, "secret_quarantined")),
            inv("membrane_generates_impressions",
                "the environmental membrane generated sensory impressions",
                lambda c: (c.get("membrane_impression_count", 0) or 0) > 0),
            inv("every_impression_has_receptor",
                "every impression carries a receptor id",
                lambda c: _truthy(c, "all_impressions_have_receptor")),
            inv("every_impression_has_source_event_ref",
                "every impression references its source event",
                lambda c: _truthy(c, "all_impressions_have_source_ref")),
            inv("operator_pulse_attenuated",
                "the operator pulse impression is attenuated",
                lambda c: _truthy(c, "operator_pulse_attenuated")),
            inv("debug_gloss_not_ground_truth",
                "debug gloss does not ground internal truth",
                lambda c: _truthy(c, "debug_gloss_not_truth")),
            inv("human_label_not_ground_truth",
                "human labels are not ground truth",
                lambda c: _truthy(c, "human_label_not_truth")),
            inv("source_pressure_report_exists",
                "a source pressure report exists",
                lambda c: _truthy(c, "source_pressure_present")),
            inv("membrane_memory_exists", "membrane memory exists",
                lambda c: _truthy(c, "membrane_memory_present")),
            inv("observation_distinguishes_diets",
                "observation distinguishes the event diet from impression diet",
                lambda c: _truthy(c, "observation_distinguishes_diets")),
            inv("ontogenesis_uses_impressions_or_marks_fallback",
                "ontogenesis (if run) uses impressions or loudly marks fallback",
                lambda c: (not c.get("ontogenesis_ran", False))
                or _truthy(c, "ontogenesis_used_impressions")
                or _truthy(c, "ontogenesis_fallback_marked"), required=False),
            inv("semiogenesis_preserves_ancestry",
                "semiogenesis (if run) preserves impression ancestry",
                lambda c: (not c.get("semiogenesis_ran", False))
                or _truthy(c, "semiogenesis_ancestry_preserved"),
                required=False),
            inv("cognition_preserves_ancestry",
                "cognition (if run) preserves impression ancestry",
                lambda c: (not c.get("cognition_ran", False))
                or _truthy(c, "cognition_ancestry_preserved"), required=False),
            inv("reports_include_disclaimers",
                "generated reports include non-claim disclaimers",
                lambda c: _truthy(c, "reports_have_disclaimers")),
            inv("no_consciousness_life_agency_claims",
                "no consciousness/life/agency claim is made",
                lambda c: _truthy(c, "claims_safe")),
            inv("no_raw_event_downstream_bypass",
                "no raw event bypassed the membrane downstream",
                lambda c: not _truthy(c, "raw_bypass_detected")),
            inv("no_feeder_hardware_network_git_shell_access",
                "no feeder/hardware/network/Git/shell access occurred",
                lambda c: _truthy(c, "no_external_access")),
        ])
