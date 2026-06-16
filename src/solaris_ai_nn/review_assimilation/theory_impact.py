"""Theory impact -- how review feedback should change a theory statement.

:class:`TheoryImpactAssessor` maps theory-level objections to theory impact
assessments. Theory impact preserves prior theory statements, prefers narrowing
over hype, keeps retired statements archived, and proves or disproves nothing about
consciousness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .objection_classifier import ObjectionCategory, ObjectionValidityStatus


class TheoryImpactType:
    SUPPORT_WORKING_HYPOTHESIS = "support_working_hypothesis"
    CHALLENGE_WORKING_HYPOTHESIS = "challenge_working_hypothesis"
    NARROW_THEORY_SCOPE = "narrow_theory_scope"
    RETIRE_THEORY_STATEMENT = "retire_theory_statement"
    REQUIRE_THEORY_REVISION = "require_theory_revision"
    REQUIRE_NEW_CONTROL = "require_new_control"
    REQUIRE_NEW_MEASUREMENT = "require_new_measurement"
    ACCEPTED_LIMITATION = "accepted_limitation"
    ACCEPTED_FALSIFICATION = "accepted_falsification"
    NO_CHANGE = "no_change"
    UNKNOWN = "unknown"

    ALL = (SUPPORT_WORKING_HYPOTHESIS, CHALLENGE_WORKING_HYPOTHESIS,
           NARROW_THEORY_SCOPE, RETIRE_THEORY_STATEMENT, REQUIRE_THEORY_REVISION,
           REQUIRE_NEW_CONTROL, REQUIRE_NEW_MEASUREMENT, ACCEPTED_LIMITATION,
           ACCEPTED_FALSIFICATION, NO_CHANGE, UNKNOWN)

    REVISIONS = (CHALLENGE_WORKING_HYPOTHESIS, NARROW_THEORY_SCOPE,
                 RETIRE_THEORY_STATEMENT, REQUIRE_THEORY_REVISION,
                 ACCEPTED_FALSIFICATION)


# objection category -> theory impact type.
_CATEGORY_IMPACT = {
    ObjectionCategory.PASSIVE_PARSER_ALTERNATIVE:
        TheoryImpactType.CHALLENGE_WORKING_HYPOTHESIS,
    ObjectionCategory.LOG_ACCUMULATION_ALTERNATIVE:
        TheoryImpactType.CHALLENGE_WORKING_HYPOTHESIS,
    ObjectionCategory.FIXTURE_OVERFIT: TheoryImpactType.NARROW_THEORY_SCOPE,
    ObjectionCategory.HUMAN_LABEL_CONTAMINATION:
        TheoryImpactType.REQUIRE_NEW_CONTROL,
    ObjectionCategory.INSUFFICIENT_CONTROLS: TheoryImpactType.REQUIRE_NEW_CONTROL,
    ObjectionCategory.INSUFFICIENT_REPLICATION:
        TheoryImpactType.REQUIRE_THEORY_REVISION,
    ObjectionCategory.UNCLEAR_METRIC: TheoryImpactType.REQUIRE_NEW_MEASUREMENT,
    ObjectionCategory.INTERPRETATION_CONCERN:
        TheoryImpactType.NARROW_THEORY_SCOPE,
    ObjectionCategory.UNSUPPORTED_CLAIM: TheoryImpactType.NARROW_THEORY_SCOPE,
    ObjectionCategory.FAILED_REPRODUCTION:
        TheoryImpactType.CHALLENGE_WORKING_HYPOTHESIS,
}


@dataclass
class TheoryImpactAssessment:
    """One theory impact (prior statements preserved; narrowing over hype)."""

    theory_id: str
    impact_type: str = TheoryImpactType.NO_CHANGE
    source_objection_id: str = ""
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.impact_type not in TheoryImpactType.ALL:
            self.impact_type = TheoryImpactType.UNKNOWN

    @property
    def is_revision(self) -> bool:
        return self.impact_type in TheoryImpactType.REVISIONS

    def to_dict(self) -> Dict[str, Any]:
        return {"theory_id": self.theory_id, "impact_type": self.impact_type,
                "source_objection_id": self.source_objection_id,
                "rationale": self.rationale, "is_revision": self.is_revision,
                "preserves_prior_statements": True,
                "proves_consciousness": False}


@dataclass
class TheoryImpactAssessor:
    """Derives theory impact from classified objections."""

    def assess(self, *, objections: List[Any],
               theory_links: Optional[Dict[str, str]] = None,
               ) -> List[TheoryImpactAssessment]:
        theory_links = theory_links or {}
        out: List[TheoryImpactAssessment] = []
        for c in objections:
            impact_type = _CATEGORY_IMPACT.get(c.category)
            if c.validity == ObjectionValidityStatus.ACCEPTED_AS_FALSIFICATION:
                impact_type = TheoryImpactType.ACCEPTED_FALSIFICATION
            elif c.validity == ObjectionValidityStatus.ACCEPTED_AS_LIMITATION:
                impact_type = TheoryImpactType.ACCEPTED_LIMITATION
            if impact_type is None:
                continue
            theory_id = theory_links.get(c.objection_id, "")
            out.append(TheoryImpactAssessment(
                theory_id=theory_id, impact_type=impact_type,
                source_objection_id=c.objection_id,
                rationale=f"from objection {c.category}: {c.text[:80]}"))
        return out

    @staticmethod
    def summary(impacts: List[TheoryImpactAssessment]) -> Dict[str, Any]:
        revisions = [i for i in impacts if i.is_revision]
        retired = [i for i in impacts
                   if i.impact_type == TheoryImpactType.RETIRE_THEORY_STATEMENT]
        return {
            "theory_impact_count": len(impacts),
            "theory_revision_count": len(revisions),
            "theory_retired_count": len(retired),
            "impacts": [i.to_dict() for i in impacts],
            "note": "theory impact preserves prior statements; narrowing is "
                    "preferred over hype; retired statements stay archived; it "
                    "proves or disproves nothing about consciousness",
        }
