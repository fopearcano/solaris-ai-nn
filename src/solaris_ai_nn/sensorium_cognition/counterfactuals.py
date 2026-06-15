"""Counterfactuals -- non-real "what if" probes that may seed hypotheses.

The :class:`CounterfactualEngine` builds :class:`Counterfactual`s ("if sign A
absent", "if source B silent", ...). Counterfactuals are marked non-real, may seed
hypotheses, and must never overwrite real traces.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class CounterfactualForm:
    SIGN_ABSENT = "if_sign_absent"
    SOURCE_SILENT = "if_source_silent"
    RELATION_FALSE = "if_relation_false"
    MODALITY_UNRELIABLE = "if_modality_unreliable"
    SIGN_SPLIT = "if_sign_split"
    CONCEPT_DECAYS = "if_concept_decays"
    ATTENTION_SHIFTS = "if_attention_shifts_to_modality"

    ALL = (SIGN_ABSENT, SOURCE_SILENT, RELATION_FALSE, MODALITY_UNRELIABLE,
           SIGN_SPLIT, CONCEPT_DECAYS, ATTENTION_SHIFTS)


@dataclass
class Counterfactual:
    """One non-real counterfactual probe (never overwrites a real trace)."""

    form: str
    target_ref: str
    counterfactual_id: str = field(
        default_factory=lambda: f"CF_{uuid.uuid4().hex[:8]}")
    expected_effect: str = ""
    seeds_hypothesis: bool = True
    evidence_refs: List[str] = field(default_factory=list)
    is_real: bool = False  # always False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "counterfactual_id": self.counterfactual_id,
            "form": self.form,
            "target_ref": self.target_ref,
            "expected_effect": self.expected_effect,
            "seeds_hypothesis": self.seeds_hypothesis,
            "evidence_refs": list(self.evidence_refs),
            "is_real": False,
            "note": "non-real counterfactual; may seed hypotheses but never "
                    "overwrites real traces",
        }


@dataclass
class CounterfactualResult:
    counterfactuals: List[Counterfactual] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"counterfactual_count": len(self.counterfactuals),
                "counterfactuals": [c.to_dict() for c in self.counterfactuals]}


@dataclass
class CounterfactualEngine:
    """Generates non-real counterfactual probes from signs and relations."""

    def generate(self, signs: List[Any], *,
                 max_counterfactuals: int = 20) -> CounterfactualResult:
        result = CounterfactualResult()
        for s in signs:
            if len(result.counterfactuals) >= max_counterfactuals:
                break
            sid = getattr(s, "sign_id", "")
            if getattr(s, "is_ambiguous", False):
                result.counterfactuals.append(Counterfactual(
                    form=CounterfactualForm.SIGN_SPLIT, target_ref=sid,
                    expected_effect="ambiguity resolved into sub-signs",
                    evidence_refs=["ambiguity"]))
            elif getattr(s, "is_absence", False):
                result.counterfactuals.append(Counterfactual(
                    form=CounterfactualForm.SIGN_ABSENT, target_ref=sid,
                    expected_effect="absence window changes uncertainty",
                    evidence_refs=["absence"]))
            else:
                result.counterfactuals.append(Counterfactual(
                    form=CounterfactualForm.SIGN_ABSENT, target_ref=sid,
                    expected_effect="downstream signs may shift",
                    evidence_refs=[getattr(s, "sign_code", sid)]))
        return result
