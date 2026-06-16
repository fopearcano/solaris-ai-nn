"""Comparison anchors -- the reference points for the next cycle's comparisons.

:class:`ComparisonAnchorSet` records the baselines/controls future replication,
soak, and architecture comparisons should measure against (parent, previous
validated, passive-parser, fixture-only, live-read-only, per-module ablations,
safety-only, ...). A missing anchor is recorded as a limitation; control anchors
are kept available even when weak.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AnchorKind:
    PARENT_BASELINE = "parent_baseline"
    PREVIOUS_VALIDATED_BASELINE = "previous_validated_baseline"
    CONTROL_BASELINE = "control_baseline"
    PASSIVE_PARSER_BASELINE = "passive_parser_baseline"
    FIXTURE_ONLY_BASELINE = "fixture_only_baseline"
    LIVE_READONLY_BASELINE = "live_readonly_baseline"
    NO_METABOLISM_BASELINE = "no_metabolism_baseline"
    NO_ONTOGENESIS_BASELINE = "no_ontogenesis_baseline"
    NO_SEMIOGENESIS_BASELINE = "no_semiogenesis_baseline"
    NO_COGNITION_BASELINE = "no_cognition_baseline"
    NO_ACTION_REACTION_BASELINE = "no_action_reaction_baseline"
    SAFETY_ONLY_BASELINE = "safety_only_baseline"
    UNKNOWN = "unknown"

    ALL = (PARENT_BASELINE, PREVIOUS_VALIDATED_BASELINE, CONTROL_BASELINE,
           PASSIVE_PARSER_BASELINE, FIXTURE_ONLY_BASELINE,
           LIVE_READONLY_BASELINE, NO_METABOLISM_BASELINE,
           NO_ONTOGENESIS_BASELINE, NO_SEMIOGENESIS_BASELINE,
           NO_COGNITION_BASELINE, NO_ACTION_REACTION_BASELINE,
           SAFETY_ONLY_BASELINE, UNKNOWN)

    # Control anchors that must remain available even if weak.
    CONTROL_KINDS = (CONTROL_BASELINE, PASSIVE_PARSER_BASELINE,
                     FIXTURE_ONLY_BASELINE, NO_METABOLISM_BASELINE,
                     NO_ONTOGENESIS_BASELINE, NO_SEMIOGENESIS_BASELINE,
                     NO_COGNITION_BASELINE, NO_ACTION_REACTION_BASELINE,
                     SAFETY_ONLY_BASELINE)


@dataclass
class ComparisonAnchor:
    """One comparison anchor (a reference baseline/control for next cycle)."""

    kind: str
    baseline_id: str = ""
    available: bool = False
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "baseline_id": self.baseline_id,
                "available": self.available, "detail": self.detail}


@dataclass
class ComparisonAnchorSet:
    """The set of comparison anchors for the next experimental cycle."""

    anchors: List[ComparisonAnchor] = field(default_factory=list)
    missing_limitations: List[str] = field(default_factory=list)

    def build(self, *, parent_baseline_id: str = "",
              previous_validated_id: str = "",
              available_anchors: Optional[Dict[str, str]] = None,
              ) -> "ComparisonAnchorSet":
        available_anchors = dict(available_anchors or {})
        if parent_baseline_id:
            available_anchors.setdefault(AnchorKind.PARENT_BASELINE,
                                         parent_baseline_id)
        if previous_validated_id:
            available_anchors.setdefault(AnchorKind.PREVIOUS_VALIDATED_BASELINE,
                                         previous_validated_id)
        for kind in AnchorKind.ALL:
            if kind == AnchorKind.UNKNOWN:
                continue
            bid = available_anchors.get(kind, "")
            available = bool(bid)
            detail = ("available reference" if available else
                      "control anchor kept available even if weak"
                      if kind in AnchorKind.CONTROL_KINDS else
                      "no anchor recorded")
            self.anchors.append(ComparisonAnchor(
                kind=kind, baseline_id=bid, available=available, detail=detail))
            if not available:
                self.missing_limitations.append(
                    f"missing comparison anchor: {kind}")
        return self

    @property
    def available_count(self) -> int:
        return sum(1 for a in self.anchors if a.available)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "comparison_anchor_count": len(self.anchors),
            "available_anchor_count": self.available_count,
            "anchors": [a.to_dict() for a in self.anchors],
            "missing_anchor_limitations": list(self.missing_limitations),
            "note": "anchors drive future replication/soak/architecture "
                    "comparisons; a missing anchor is a limitation, and control "
                    "anchors stay available even if weak",
        }
