"""CausalTraceBuilder -- approximate chains from what was actually recorded.

The builder reconstructs chains like::

    Stimulus -> substrate update -> readout tendency -> action -> Reaction
             -> readout update -> habit reinforcement

from the bridge's trace memory (event/action/reaction records). Honesty rule:
only relations that are *directly coded* in the system (a Reaction literally
triggers the readout update and habit reinforcement) carry the relation
``caused`` with confidence 1.0. Everything reconstructed from temporal order is
``preceded`` / ``was_associated_with`` / ``influenced`` with confidence < 1.0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .schemas import CausalLink, CausalTrace, Explanation

# Relations allowed for heuristic (non-coded) links.
HEDGED_RELATIONS = ("preceded", "was_associated_with", "influenced")


@dataclass
class CausalTraceBuilder:
    """Builds bounded causal traces from recorded runtime history."""

    traces: Dict[str, CausalTrace] = field(default_factory=dict)
    _current: Optional[CausalTrace] = field(default=None, init=False)

    def _ensure(self) -> CausalTrace:
        if self._current is None:
            self._current = CausalTrace()
            self.traces[self._current.chain_id] = self._current
        return self._current

    def link(self, source: str, target: str, relation: str,
             confidence: float, metadata: Optional[Dict[str, Any]] = None) -> CausalLink:
        """Add one link; hedged relations are enforced for confidence < 1.0."""
        if confidence < 0.99 and relation not in HEDGED_RELATIONS:
            # Never let a heuristic link carry a hard causal verb.
            relation = "was_associated_with"
        link = CausalLink(source=source, target=target, relation=relation,
                          confidence=confidence, metadata=dict(metadata or {}))
        self._ensure().links.append(link)
        return link

    def build_from_recent_trace(self, trace: Any, max_depth: int = 8) -> CausalTrace:
        """Reconstruct a chain from a TraceMemory's recent records.

        ``trace`` is a `memory.trace_memory.TraceMemory` (records with
        categories "event" / "action" / "reaction").
        """
        self._current = CausalTrace()
        self.traces[self._current.chain_id] = self._current
        records = list(getattr(trace, "records", []))[-max_depth * 3:]

        last_event: Optional[str] = None
        last_action: Optional[str] = None
        depth = 0
        for rec in records:
            if depth >= max_depth:
                break
            data = rec.data
            if rec.category == "event":
                label = f"{data.get('kind', 'event')}(step {rec.step})"
                if last_event is None:
                    last_event = label
                    continue
                last_event = label
            elif rec.category == "action" and last_event is not None:
                label = f"action {data.get('action', '?')}(step {rec.step})"
                # Heuristic: the event stream shaped the tendency.
                self.link(last_event, "substrate update", "preceded", 0.9)
                self.link("substrate update", label, "influenced", 0.7,
                          {"mechanism": "readout tendency over substrate state"})
                last_action = label
                depth += 1
            elif rec.category == "reaction" and last_action is not None:
                valence = data.get("valence", 0.0)
                label = f"Reaction(valence {valence:+.2f}, step {rec.step})"
                self.link(last_action, label, "was_associated_with", 0.7)
                # These two ARE directly coded paths (bridge.react does both).
                self.link(label, "readout update", "caused", 1.0,
                          {"mechanism": "online NLMS update in bridge.react"})
                self.link(label, "habit reinforcement", "caused", 1.0,
                          {"mechanism": "HabitReinforcement.observe in bridge.react"})
                depth += 1
        return self._current

    def explain_chain(self, chain_id: str) -> Explanation:
        """Render one chain as a hedged, grounded explanation."""
        chain = self.traces.get(chain_id)
        if chain is None or not chain.links:
            return Explanation(
                topic="causal_chain",
                text="The system does not know: no causal chain with that id "
                     "has been built.",
                unknowns=[f"chain {chain_id!r}"], confidence=0.0)
        lines = [link.sentence() for link in chain.links]
        heuristic = sum(1 for l in chain.links if l.confidence < 0.99)
        text = ("Reconstructed chain (heuristic links are associations, not "
                "proven causation): " + "; ".join(lines) + ".")
        return Explanation(
            topic="causal_chain", text=text,
            grounded_in=[f"links={len(chain.links)}",
                         f"heuristic_links={heuristic}"],
            confidence=min((l.confidence for l in chain.links), default=1.0))
