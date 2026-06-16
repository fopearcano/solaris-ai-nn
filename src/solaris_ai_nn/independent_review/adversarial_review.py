"""Adversarial review -- alternative explanations, preserved and never dismissed.

:class:`AdversarialReviewEngine` generates the alternative (deflationary)
explanations a hostile reviewer would raise for any apparent result (log
accumulation, fixture overfit, human-label leakage, passive-parser artifact, random
seed artifact, reporting bias, missing control, insufficient runtime/replication,
cherry-picked examples, operator confirmation bias, ClaimGuard blind spot,
measurement artifact, source-diet artifact, safety-boundary artifact). Alternative
explanations are preserved, never auto-dismissed, each lists the evidence needed to
reduce its uncertainty, and a strong alternative downgrades review readiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AlternativeExplanationType:
    LOG_ACCUMULATION = "log_accumulation"
    FIXTURE_OVERFIT = "fixture_overfit"
    HUMAN_LABEL_LEAKAGE = "human_label_leakage"
    PASSIVE_PARSER_ARTIFACT = "passive_parser_artifact"
    RANDOM_SEED_ARTIFACT = "random_seed_artifact"
    REPORTING_BIAS = "reporting_bias"
    MISSING_CONTROL = "missing_control"
    INSUFFICIENT_RUNTIME = "insufficient_runtime"
    INSUFFICIENT_REPLICATION = "insufficient_replication"
    CHERRY_PICKED_EXAMPLES = "cherry_picked_examples"
    OPERATOR_CONFIRMATION_BIAS = "operator_confirmation_bias"
    CLAIMGUARD_BLIND_SPOT = "claimguard_blind_spot"
    MEASUREMENT_ARTIFACT = "measurement_artifact"
    SOURCE_DIET_ARTIFACT = "source_diet_artifact"
    SAFETY_BOUNDARY_ARTIFACT = "safety_boundary_artifact"

    ALL = (LOG_ACCUMULATION, FIXTURE_OVERFIT, HUMAN_LABEL_LEAKAGE,
           PASSIVE_PARSER_ARTIFACT, RANDOM_SEED_ARTIFACT, REPORTING_BIAS,
           MISSING_CONTROL, INSUFFICIENT_RUNTIME, INSUFFICIENT_REPLICATION,
           CHERRY_PICKED_EXAMPLES, OPERATOR_CONFIRMATION_BIAS,
           CLAIMGUARD_BLIND_SPOT, MEASUREMENT_ARTIFACT, SOURCE_DIET_ARTIFACT,
           SAFETY_BOUNDARY_ARTIFACT)


# type -> (explanation text, evidence needed to reduce uncertainty).
_SPECS = {
    AlternativeExplanationType.LOG_ACCUMULATION:
        ("Apparent growth could be raw log accumulation, not development.",
         "growth-vs-log-size comparison over time"),
    AlternativeExplanationType.FIXTURE_OVERFIT:
        ("The result could be specific to the test fixtures.",
         "live-field or held-out fixture replication"),
    AlternativeExplanationType.HUMAN_LABEL_LEAKAGE:
        ("The structure could come from human labels, not the data.",
         "random-labels-same-features control"),
    AlternativeExplanationType.PASSIVE_PARSER_ARTIFACT:
        ("A passive parser might produce the same apparent structure.",
         "passive-parser control comparison"),
    AlternativeExplanationType.RANDOM_SEED_ARTIFACT:
        ("The effect could be a lucky random seed.",
         "replication across multiple seeds"),
    AlternativeExplanationType.REPORTING_BIAS:
        ("Only the runs that worked may have been reported.",
         "complete run registry including failed runs"),
    AlternativeExplanationType.MISSING_CONTROL:
        ("Without a matched control, the effect is uninterpretable.",
         "ablation/null control arm with equal opportunity"),
    AlternativeExplanationType.INSUFFICIENT_RUNTIME:
        ("The runtime may be too short for the developmental claim.",
         "longer soak with the same protocol"),
    AlternativeExplanationType.INSUFFICIENT_REPLICATION:
        ("Too few runs to distinguish signal from noise.",
         "additional independent replication arms"),
    AlternativeExplanationType.CHERRY_PICKED_EXAMPLES:
        ("The examples shown may be unrepresentative.",
         "full distribution of examples, not selected ones"),
    AlternativeExplanationType.OPERATOR_CONFIRMATION_BIAS:
        ("The operator may have read the result they expected.",
         "pre-registered metric and blinded scoring"),
    AlternativeExplanationType.CLAIMGUARD_BLIND_SPOT:
        ("ClaimGuard may miss novel overclaiming wording.",
         "independent re-read of all generated text"),
    AlternativeExplanationType.MEASUREMENT_ARTIFACT:
        ("The metric could measure an artifact, not the construct.",
         "construct-validity check against an independent metric"),
    AlternativeExplanationType.SOURCE_DIET_ARTIFACT:
        ("The result could depend on the specific source diet.",
         "varied source diet replication"),
    AlternativeExplanationType.SAFETY_BOUNDARY_ARTIFACT:
        ("The result could be an artifact of a safety boundary.",
         "boundary-on vs boundary-documented comparison"),
}

# Alternatives considered "strong" when the matching bundle signal is present.
_STRONG_SIGNALS = {
    AlternativeExplanationType.LOG_ACCUMULATION: "log_accumulation_warning",
    AlternativeExplanationType.FIXTURE_OVERFIT: "fixture_overfit_risk",
    AlternativeExplanationType.HUMAN_LABEL_LEAKAGE: "label_contamination_risk",
    AlternativeExplanationType.PASSIVE_PARSER_ARTIFACT:
        "passive_parser_equivalent",
    AlternativeExplanationType.INSUFFICIENT_REPLICATION: "missing_replication",
    AlternativeExplanationType.MISSING_CONTROL: "missing_control",
}


@dataclass
class AlternativeExplanation:
    """One deflationary alternative explanation (preserved, never dismissed)."""

    explanation_type: str
    text: str
    evidence_needed: str
    strong: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"explanation_type": self.explanation_type, "text": self.text,
                "evidence_needed": self.evidence_needed, "strong": self.strong,
                "auto_dismissed": False}


@dataclass
class AdversarialReviewFinding:
    """The set of alternative explanations against the current evidence."""

    explanations: List[AlternativeExplanation] = field(default_factory=list)

    @property
    def strong(self) -> List[AlternativeExplanation]:
        return [e for e in self.explanations if e.strong]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adversarial_finding_count": len(self.explanations),
            "alternative_explanation_count": len(self.explanations),
            "strong_alternative_count": len(self.strong),
            "explanations": [e.to_dict() for e in self.explanations],
            "note": "alternative explanations are preserved and never "
                    "auto-dismissed; a strong alternative downgrades review "
                    "readiness",
        }


@dataclass
class AdversarialReviewEngine:
    """Generates and preserves alternative explanations from the bundle."""

    def review(self, bundle: Dict[str, Any]) -> AdversarialReviewFinding:
        bundle = bundle or {}
        signals = self._signals(bundle)
        explanations: List[AlternativeExplanation] = []
        for etype in AlternativeExplanationType.ALL:
            text, evidence_needed = _SPECS[etype]
            signal_key = _STRONG_SIGNALS.get(etype)
            strong = bool(signal_key and signals.get(signal_key))
            explanations.append(AlternativeExplanation(
                explanation_type=etype, text=text,
                evidence_needed=evidence_needed, strong=strong))
        return AdversarialReviewFinding(explanations=explanations)

    @staticmethod
    def _signals(bundle: Dict[str, Any]) -> Dict[str, bool]:
        diff = bundle.get("sensorium_differentiation", {}) or {}
        soak = bundle.get("soak", {}) or {}
        repl = bundle.get("replication", {}) or {}
        ce = bundle.get("counterevidence", {}) or {}
        ce_types = {r.get("counter_type")
                    for r in (ce.get("records", []) or [])}
        return {
            "log_accumulation_warning": bool(
                soak.get("log_accumulation_warning")
                or bundle.get("log_accumulation_warning")
                or "log_accumulation_warning" in ce_types),
            "fixture_overfit_risk": bool(
                diff.get("fixture_overfit_risk")
                or bundle.get("fixture_overfit_risk")
                or "fixture_overfit" in ce_types),
            "label_contamination_risk": bool(
                diff.get("label_contamination_risk")
                or bundle.get("label_contamination_risk")
                or "human_label_dependency" in ce_types),
            "passive_parser_equivalent": bool(
                diff.get("passive_parser_equivalent")
                or bundle.get("passive_parser_equivalent")
                or "passive_parser_equivalence" in ce_types),
            "missing_replication": bool(
                not bundle.get("replication")
                or int(repl.get("replication_arm_count", 0) or 0) == 0),
            "missing_control": bool(bundle.get("missing_control")),
        }
