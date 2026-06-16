"""Limitations builder -- mandatory, specific, first-class limitations.

:class:`LimitationsBuilder` produces the limitation statements that every claim
report and dossier must carry. Limitations are mandatory and specific; they are
linked to the claims they constrain (not buried at the end only); and the "no
consciousness / subjective / agency / real-world actuation evidence" limitations
are always present.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LimitationCategory:
    MISSING_REPLICATION = "missing_replication"
    MISSING_LIVE_DATA = "missing_live_data"
    FIXTURE_DEPENDENCE = "fixture_dependence"
    LABEL_CONTAMINATION = "label_contamination"
    WEAK_CONTROLS = "weak_controls"
    SHORT_RUNTIME = "short_runtime"
    INSUFFICIENT_SAMPLE_SIZE = "insufficient_sample_size"
    RESOURCE_CONSTRAINTS = "resource_constraints"
    MEASUREMENT_LIMITS = "measurement_limits"
    MODULE_INCOMPLETENESS = "module_incompleteness"
    SAFETY_BOUNDARY_LIMITS = "safety_boundary_limits"
    NO_CONSCIOUSNESS_EVIDENCE = "no_consciousness_evidence"
    NO_SUBJECTIVE_EVIDENCE = "no_subjective_evidence"
    NO_AGENCY_EVIDENCE = "no_agency_evidence"
    NO_REAL_WORLD_ACTUATION = "no_real_world_actuation"

    ALL = (MISSING_REPLICATION, MISSING_LIVE_DATA, FIXTURE_DEPENDENCE,
           LABEL_CONTAMINATION, WEAK_CONTROLS, SHORT_RUNTIME,
           INSUFFICIENT_SAMPLE_SIZE, RESOURCE_CONSTRAINTS, MEASUREMENT_LIMITS,
           MODULE_INCOMPLETENESS, SAFETY_BOUNDARY_LIMITS,
           NO_CONSCIOUSNESS_EVIDENCE, NO_SUBJECTIVE_EVIDENCE, NO_AGENCY_EVIDENCE,
           NO_REAL_WORLD_ACTUATION)

    # Mandatory limitations present in every report.
    MANDATORY = (NO_CONSCIOUSNESS_EVIDENCE, NO_SUBJECTIVE_EVIDENCE,
                 NO_AGENCY_EVIDENCE, NO_REAL_WORLD_ACTUATION)


_MANDATORY_TEXT = {
    LimitationCategory.NO_CONSCIOUSNESS_EVIDENCE:
        "No evidence of consciousness, sentience, or biological life exists or "
        "is claimed; no such measurement is performed.",
    LimitationCategory.NO_SUBJECTIVE_EVIDENCE:
        "No evidence of subjective experience, feeling, or emotion exists or is "
        "claimed; the system reports operational structures only.",
    LimitationCategory.NO_AGENCY_EVIDENCE:
        "No evidence of agency, free will, personhood, or self-awareness exists "
        "or is claimed.",
    LimitationCategory.NO_REAL_WORLD_ACTUATION:
        "The system performs no real-world actuation and controls no hardware; "
        "all evidence is from bounded local fixtures or read-only feeds.",
}


@dataclass
class LimitationStatement:
    """One specific limitation, linked to the claims it constrains."""

    category: str
    text: str
    claim_refs: List[str] = field(default_factory=list)
    detail: str = ""

    def __post_init__(self) -> None:
        if self.category not in LimitationCategory.ALL:
            self.category = LimitationCategory.MEASUREMENT_LIMITS

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "text": self.text,
                "claim_refs": list(self.claim_refs), "detail": self.detail,
                "mandatory": self.category in LimitationCategory.MANDATORY}


@dataclass
class LimitationsBuilder:
    """Builds the mandatory + evidence-derived limitation statements."""

    def build(self, bundle: Dict[str, Any], *,
              claim_refs: Optional[List[str]] = None,
              ) -> List[LimitationStatement]:
        bundle = bundle or {}
        refs = list(claim_refs or [])
        out: List[LimitationStatement] = []

        # Mandatory limitations are always first-class.
        for cat in LimitationCategory.MANDATORY:
            out.append(LimitationStatement(category=cat,
                                           text=_MANDATORY_TEXT[cat],
                                           claim_refs=refs))

        repl = bundle.get("replication", {}) or {}
        diff = bundle.get("sensorium_differentiation", {}) or {}
        soak = bundle.get("soak", {}) or {}

        if not bundle.get("replication") or \
                int(repl.get("replication_arm_count", 0) or 0) == 0:
            out.append(LimitationStatement(
                LimitationCategory.MISSING_REPLICATION,
                "Results are not yet replicated across independent runs.", refs))
        if bundle.get("missing_live_data") or not bundle.get("live_field"):
            out.append(LimitationStatement(
                LimitationCategory.MISSING_LIVE_DATA,
                "Evidence is from fixtures; no live-field data confirms it.",
                refs))
        if diff.get("fixture_overfit_risk") or bundle.get("fixture_overfit_risk"):
            out.append(LimitationStatement(
                LimitationCategory.FIXTURE_DEPENDENCE,
                "Results may be specific to the test fixtures used.", refs))
        if diff.get("label_contamination_risk") or \
                bundle.get("label_contamination_risk"):
            out.append(LimitationStatement(
                LimitationCategory.LABEL_CONTAMINATION,
                "Results may depend on human-supplied labels.", refs))
        if bundle.get("weak_controls"):
            out.append(LimitationStatement(
                LimitationCategory.WEAK_CONTROLS,
                "Control comparisons are weak or incomplete.", refs))
        if bundle.get("short_runtime") or soak.get("short_runtime"):
            out.append(LimitationStatement(
                LimitationCategory.SHORT_RUNTIME,
                "Runtime is short relative to the developmental claims.", refs))
        if bundle.get("insufficient_sample_size"):
            out.append(LimitationStatement(
                LimitationCategory.INSUFFICIENT_SAMPLE_SIZE,
                "Sample size is small; statistical confidence is limited.", refs))
        for cat, key in ((LimitationCategory.RESOURCE_CONSTRAINTS,
                          "resource_constraints"),
                         (LimitationCategory.MEASUREMENT_LIMITS,
                          "measurement_limits"),
                         (LimitationCategory.MODULE_INCOMPLETENESS,
                          "module_incompleteness"),
                         (LimitationCategory.SAFETY_BOUNDARY_LIMITS,
                          "safety_boundary_limits")):
            if bundle.get(key):
                out.append(LimitationStatement(
                    cat, str(bundle.get(key)), refs))
        return out

    @staticmethod
    def summary(limitations: List[LimitationStatement]) -> Dict[str, Any]:
        return {
            "limitation_count": len(limitations),
            "mandatory_count": sum(
                1 for l in limitations
                if l.category in LimitationCategory.MANDATORY),
            "limitations": [l.to_dict() for l in limitations],
            "note": "limitations are mandatory and specific; they are linked to "
                    "the claims they constrain and are not buried at the end only",
        }
