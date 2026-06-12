"""Semantic grounding -- a symbol means what it reliably co-occurs with.

Meaning here is operational grounding, not human understanding: each
symbol is tied to the signal patterns, contexts, needs, actions,
reactions, world-model nodes, boundaries, schemas, milestones, Mysterium
changes, and executive decisions it was observed with. Ambiguity (many
inconsistent groundings) stays measured and visible; real, simulated,
offline, and counterfactual evidence are never mixed up.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .symbols import ProtoSymbol, SymbolGrounding

GROUNDING_DIMENSIONS = (
    "signal_pattern", "context", "need_state", "action_tendency",
    "reaction_valence", "world_model_node", "boundary", "latent_schema",
    "milestone", "mysterium_change", "executive_decision",
)

MEANING_NOTE = ("meaning here is operational grounding -- reliable "
                "co-occurrence with recorded structure -- not human "
                "understanding")


@dataclass
class GroundedMeaning:
    """The full grounding picture for one symbol."""

    symbol_id: str
    token: str = ""
    dimensions: Dict[str, List[str]] = field(default_factory=dict)
    evidence_kinds: Dict[str, int] = field(default_factory=dict)
    ambiguity: float = 0.0
    stability: float = 0.0
    note: str = MEANING_NOTE
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SemanticGroundingEngine:
    """Builds and maintains the grounding picture per symbol."""

    meanings: Dict[str, GroundedMeaning] = field(default_factory=dict)
    groundings_made: int = field(default=0, init=False)

    def ground_symbol(self, symbol: ProtoSymbol,
                      context: Optional[Dict[str, Any]] = None,
                      ) -> GroundedMeaning:
        """Tie the symbol to whatever the context dimensions offer."""
        ctx = dict(context or {})
        meaning = self.meanings.get(symbol.symbol_id) \
            or GroundedMeaning(symbol_id=symbol.symbol_id,
                               token=symbol.token)
        evidence_kind = str(ctx.get("evidence_kind", "real"))
        for dimension in GROUNDING_DIMENSIONS:
            value = ctx.get(dimension)
            if value is None:
                continue
            values = meaning.dimensions.setdefault(dimension, [])
            text = str(value)[:80]
            if text not in values:
                values.append(text)
                meaning.dimensions[dimension] = values[-10:]
            symbol.observe(f"{dimension}:{text}",
                           evidence_kind=evidence_kind,
                           dimension=dimension)
        meaning.evidence_kinds[evidence_kind] = \
            meaning.evidence_kinds.get(evidence_kind, 0) + 1
        meaning.ambiguity = self.measure_ambiguity(symbol, meaning)
        meaning.stability = self.measure_stability(symbol, meaning)
        meaning.updated_at = time.time()
        symbol.ambiguity_score = meaning.ambiguity
        symbol.stability_score = meaning.stability
        symbol.recompute_confidence()
        self.meanings[symbol.symbol_id] = meaning
        self.groundings_made += 1
        return meaning

    def update_grounding(self, symbol: ProtoSymbol,
                         new_evidence: Dict[str, Any],
                         ) -> GroundedMeaning:
        return self.ground_symbol(symbol, new_evidence)

    # -- measurements ---------------------------------------------------------------

    def measure_ambiguity(self, symbol: ProtoSymbol,
                          meaning: Optional[GroundedMeaning] = None,
                          ) -> float:
        """Many distinct values per dimension == an ambiguous sign."""
        meaning = meaning or self.meanings.get(symbol.symbol_id)
        if meaning is None or not meaning.dimensions:
            return 0.5  # ungrounded symbols are ambiguous by default
        spreads = [min(1.0, (len(values) - 1) / 4.0)
                   for values in meaning.dimensions.values()]
        return round(sum(spreads) / len(spreads), 4)

    def measure_stability(self, symbol: ProtoSymbol,
                          meaning: Optional[GroundedMeaning] = None,
                          ) -> float:
        """Repetition with consistent grounding == a stable sign."""
        meaning = meaning or self.meanings.get(symbol.symbol_id)
        repetition = min(1.0, symbol.observation_count / 10.0)
        consistency = 1.0 - self.measure_ambiguity(symbol, meaning)
        return round(0.5 * repetition + 0.5 * consistency, 4)

    def evidence_kind_summary(self, symbol: ProtoSymbol,
                              ) -> Dict[str, int]:
        meaning = self.meanings.get(symbol.symbol_id)
        return dict(meaning.evidence_kinds) if meaning else {}

    def snapshot(self) -> Dict[str, Any]:
        ambiguities = [m.ambiguity for m in self.meanings.values()]
        return {
            "grounded_symbol_count": len(self.meanings),
            "groundings_made": self.groundings_made,
            "mean_ambiguity": (round(sum(ambiguities)
                                     / len(ambiguities), 4)
                               if ambiguities else None),
            "dimensions": list(GROUNDING_DIMENSIONS),
            "note": MEANING_NOTE,
        }
