"""Symbol emergence -- repetition earns a name; nothing else does.

The engine scans recorded context (meaning traces, habits, Mysterium
spikes, boundary events, executive inhibitions, world-model entities,
needs, latent schemas, milestones) for patterns above a repetition
threshold and proposes symbol candidates -- each with evidence references,
deterministically named, no LLM, no human feedback. Candidates born from
counterfactual evidence must be marked offline or they are rejected.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .symbol_registry import SymbolRegistry
from .symbols import ProtoSymbol, SymbolType


@dataclass
class SymbolCandidate:
    """One pattern that may deserve a sign."""

    symbol_type: str
    grounding_summary: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    repetition_count: int = 0
    trigger: str = ""
    evidence_kind: str = "real"
    offline: bool = False
    source_module: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


# (context key, symbol type, trigger description, source module).
_SCAN_RULES = (
    ("repeated_stimulus_patterns", SymbolType.STIMULUS,
     "repeated stimulus pattern above threshold", "meaning_trace"),
    ("absence_states", SymbolType.ABSENCE,
     "recurring absence/silence state", "meaning_trace"),
    ("action_reaction_loops", SymbolType.HABIT,
     "stable habit loop", "habit"),
    ("repeated_actions", SymbolType.ACTION,
     "recurring action suggestion", "executive"),
    ("repeated_reactions", SymbolType.REACTION,
     "recurring reaction pattern", "bridge"),
    ("mysterium_spikes", SymbolType.UNKNOWN,
     "repeated unknown/Mysterium spike", "mysterium"),
    ("boundary_events", SymbolType.BOUNDARY,
     "recurring boundary event", "ego"),
    ("self_boundary_events", SymbolType.SELF_BOUNDARY,
     "recurring self-boundary event", "ego"),
    ("executive_inhibitions", SymbolType.EXECUTIVE_DECISION,
     "recurring executive inhibition", "executive"),
    ("need_pressures", SymbolType.NEED,
     "recurring need pressure", "homeostasis"),
    ("world_model_entities", SymbolType.ENTITY,
     "recurring world-model entity", "world_model"),
    ("world_model_contexts", SymbolType.CONTEXT,
     "recurring world-model context", "world_model"),
    ("latent_schemas", SymbolType.LATENT_SCHEMA,
     "consolidated latent schema", "latent"),
    ("milestones", SymbolType.MILESTONE,
     "developmental milestone", "developmental"),
    ("pilot_stream_patterns", SymbolType.STIMULUS,
     "repeated pilot stream pattern (observation only)", "pilot"),
)


@dataclass
class SymbolEmergenceEngine:
    """Scans context counts; proposes, accepts, and rejects candidates."""

    registry: SymbolRegistry
    min_repetition: int = 3
    candidates_proposed: int = field(default=0, init=False)
    candidates_accepted: int = field(default=0, init=False)
    candidates_rejected: int = field(default=0, init=False)
    rejections: List[Dict[str, Any]] = field(default_factory=list,
                                             init=False)

    # -- scanning -----------------------------------------------------------------

    def scan_context(self, context: Dict[str, Any],
                     ) -> List[SymbolCandidate]:
        """Context counts -> candidates. Deterministic, evidence-backed."""
        candidates: List[SymbolCandidate] = []
        for key, symbol_type, trigger, module in _SCAN_RULES:
            entries = context.get(key) or {}
            if isinstance(entries, list):
                entries = {str(e): self.min_repetition for e in entries}
            for pattern, count in sorted(entries.items()):
                count = int(count or 0)
                # Milestones and schemas are singular by nature.
                threshold = (1 if symbol_type in
                             (SymbolType.MILESTONE,
                              SymbolType.LATENT_SCHEMA)
                             else self.min_repetition)
                if count < threshold:
                    continue
                offline = bool(context.get("offline_replay")) \
                    or module == "latent"
                candidates.append(SymbolCandidate(
                    symbol_type=symbol_type,
                    grounding_summary=str(pattern),
                    evidence_refs=[f"{key}:{pattern}",
                                   f"count:{count}"],
                    repetition_count=count, trigger=trigger,
                    evidence_kind=("offline" if offline else
                                   str(context.get("evidence_kind",
                                                   "real"))),
                    offline=offline, source_module=module))
        self.candidates_proposed += len(candidates)
        return candidates

    def propose_symbols(self, candidates: List[SymbolCandidate],
                        ) -> List[ProtoSymbol]:
        accepted: List[ProtoSymbol] = []
        for candidate in candidates:
            symbol = self.accept_symbol(candidate)
            if symbol is not None:
                accepted.append(symbol)
        return accepted

    def accept_symbol(self, candidate: SymbolCandidate,
                      ) -> Optional[ProtoSymbol]:
        if not candidate.evidence_refs:
            return self.reject_symbol(candidate,
                                      "no evidence references")
        if candidate.evidence_kind == "counterfactual" \
                and not candidate.offline:
            return self.reject_symbol(
                candidate, "counterfactual evidence must be marked "
                           "offline; counterfactuals never become real "
                           "grounding")
        symbol = self.registry.upsert_symbol(
            symbol_type=candidate.symbol_type,
            grounding_summary=candidate.grounding_summary,
            evidence_refs=candidate.evidence_refs,
            source_module=candidate.source_module,
            evidence_kind=candidate.evidence_kind,
            offline=candidate.offline,
            metadata={"trigger": candidate.trigger,
                      "repetition_count": candidate.repetition_count})
        self.candidates_accepted += 1
        return symbol

    def reject_symbol(self, candidate: SymbolCandidate,
                      reason: str) -> None:
        self.candidates_rejected += 1
        self.rejections.append({"candidate": candidate.to_dict(),
                                "reason": reason})
        self.rejections = self.rejections[-50:]
        return None

    def snapshot(self) -> Dict[str, Any]:
        return {
            "candidates_proposed": self.candidates_proposed,
            "candidates_accepted": self.candidates_accepted,
            "candidates_rejected": self.candidates_rejected,
            "recent_rejections": self.rejections[-3:],
            "min_repetition": self.min_repetition,
            "note": "repetition earns a name; no LLM naming, no human "
                    "feedback, evidence required",
        }
