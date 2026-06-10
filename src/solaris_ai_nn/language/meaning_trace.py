"""MeaningTraceBuilder -- runtime happenings become controlled-vocabulary atoms.

The builder consumes what the system already records (signals, bridge
snapshots, Inner MAP snapshots, embodiment action results, plasticity results)
and emits :class:`MeaningAtom` statements through the controlled vocabulary.
Every atom is grounded in a concrete field of its source; nothing is inferred
beyond what the source object states.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .schemas import MeaningAtom, MeaningTrace
from .vocabulary import normalize_category, normalize_predicate


def atom(category: str, subject: str, predicate: str, value: Any = None,
         confidence: float = 1.0, source_module: str = "",
         source_signal_id: Any = None, **metadata: Any) -> MeaningAtom:
    """Build one vocabulary-normalised meaning atom."""
    return MeaningAtom(
        category=normalize_category(category),
        subject=subject,
        predicate=normalize_predicate(predicate),
        value=value, confidence=confidence, source_module=source_module,
        source_signal_id=source_signal_id, metadata=dict(metadata))


@dataclass
class MeaningTraceBuilder:
    """Accumulates a bounded meaning trace from runtime sources."""

    capacity: int = 2_000
    atoms: List[MeaningAtom] = field(default_factory=list)
    dropped: int = 0

    # -- converters -----------------------------------------------------------

    def from_signal(self, signal: Any,
                    context: Optional[Dict[str, Any]] = None) -> List[MeaningAtom]:
        """Atoms describing one canonical (or duck-typed) signal."""
        kind = getattr(signal, "kind", type(signal).__name__)
        sid = getattr(signal, "id", None)
        origin = getattr(signal, "origin", "unknown")
        out = [atom("signal", kind, "received", f"from {origin}",
                    source_module="bridge", source_signal_id=sid)]
        intensity = float(getattr(signal, "intensity", 0.0) or 0.0)
        if intensity >= 0.7:
            out.append(atom("signal", f"{kind} intensity", "updated",
                            f"high ({intensity:.2f})", source_signal_id=sid))
        if getattr(signal, "is_absence", False):
            out.append(atom("signal", "absence stimulus", "received",
                            "no meaningful input sensed", source_signal_id=sid))
        valence = getattr(signal, "valence", None)
        if kind == "Reaction" and valence is not None:
            direction = ("negative" if valence < 0
                         else "positive" if valence > 0 else "neutral")
            out.append(atom("signal", "Reaction valence", "received",
                            f"{direction} ({float(valence):+.2f})",
                            source_signal_id=sid))
        fracture = getattr(signal, "fracture", None)
        if kind == "LogosTension" and fracture is not None:
            out.append(atom("signal", "Logos fracture", "influenced",
                            f"{float(fracture):.2f}", confidence=0.9,
                            source_signal_id=sid))
        if context:
            out.append(atom("signal", kind, "encoded_as",
                            f"vector(len={context.get('vector_len', 'unknown')}, "
                            f"norm={context.get('vector_norm', 'unknown')})",
                            source_module="encoder", source_signal_id=sid))
        return out

    def from_bridge_snapshot(self, snapshot: Dict[str, Any]) -> List[MeaningAtom]:
        """Atoms describing the bridge/substrate state after a step."""
        out = [atom("substrate",
                    f"{snapshot.get('substrate_type', 'substrate')} state",
                    "updated",
                    f"norm={snapshot.get('substrate_state_norm', 0.0):.4f}",
                    source_module="bridge")]
        action = snapshot.get("last_suggested_action")
        if action is not None:
            out.append(atom("readout", "action tendency", "suggested",
                            f"{action} (confidence "
                            f"{snapshot.get('last_confidence', 0.0)})",
                            source_module="readout"))
        pathways = snapshot.get("habit_pathways", 0)
        if pathways:
            out.append(atom("habit", "habit pathways", "updated",
                            f"count={pathways}", source_module="habit"))
        return out

    def from_inner_map(self, snapshot: Dict[str, Any]) -> List[MeaningAtom]:
        """Atoms describing continuity/plasticity/embodiment in the Inner MAP."""
        out: List[MeaningAtom] = []
        continuity = snapshot.get("continuity", {}) or {}
        if continuity.get("restart_count", 0) > 0:
            out.append(atom("continuity", "session", "restored",
                            f"restart #{continuity['restart_count']}",
                            source_module="inner_map"))
        gap = continuity.get("brain_death_gap_seconds", 0.0)
        if gap and gap > 0.0:
            out.append(atom("continuity", "brain-death gap", "received",
                            f"{gap:.3f}s", source_module="inner_map"))
        plasticity = snapshot.get("plasticity", {}) or {}
        if plasticity.get("pruning_count", 0) > 0:
            out.append(atom("synthesis", "weak pathways", "pruned",
                            f"{plasticity.get('removed_pathway_count', 0)} removed "
                            f"in {plasticity['pruning_count']} passes",
                            source_module="synthesis"))
        if snapshot.get("embodiment"):
            out.append(atom("embodiment", "simulated body", "updated",
                            f"position {snapshot['embodiment'].get('position')}",
                            source_module="embodiment"))
        return out

    def from_embodiment_result(self, result: Dict[str, Any]) -> List[MeaningAtom]:
        """Atoms describing one simulated action result (dict form)."""
        action = result.get("action", "unknown")
        out: List[MeaningAtom] = []
        if result.get("executed"):
            out.append(atom("embodiment", f"action {action}", "succeeded",
                            result.get("consequence", ""),
                            source_module="effectors"))
        else:
            out.append(atom("safety" if "safety" in str(result.get("blocked_reason", ""))
                            else "embodiment",
                            f"action {action}", "blocked",
                            result.get("blocked_reason", "unknown"),
                            source_module="embodiment_safety"))
        for event in result.get("events", []):
            if str(event).startswith("touched:"):
                out.append(atom("embodiment", f"object {event.split(':', 1)[1]}",
                                "updated", "touched", source_module="effectors"))
        return out

    def from_plasticity_result(self, result: Dict[str, Any]) -> List[MeaningAtom]:
        """Atoms describing one plasticity apply/reject result (dict form)."""
        status = result.get("status", "unknown")
        target = result.get("step_id", "step")
        if result.get("applied"):
            return [atom("plasticity", f"parameter ({target})", "updated",
                         f"{result.get('old_value')} -> {result.get('new_value')}",
                         source_module="plasticity_engine")]
        if status == "rejected":
            return [atom("plasticity", f"proposal ({target})", "blocked",
                         result.get("message", "rejected by safety"),
                         source_module="safety_validator")]
        return [atom("plasticity", f"proposal ({target})", "influenced",
                     result.get("message", status), confidence=0.8,
                     source_module="plasticity_engine")]

    # -- accumulation -----------------------------------------------------------

    def append_atoms(self, atoms: List[MeaningAtom]) -> None:
        self.atoms.extend(atoms)
        if len(self.atoms) > self.capacity:
            self.dropped += len(self.atoms) - self.capacity
            self.atoms = self.atoms[-self.capacity:]

    def record(self, *converted: List[MeaningAtom]) -> None:
        for atoms in converted:
            self.append_atoms(atoms)

    def __len__(self) -> int:
        return len(self.atoms)

    def category_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for a in self.atoms:
            counts[a.category] = counts.get(a.category, 0) + 1
        return counts

    def snapshot(self) -> Dict[str, Any]:
        return {
            "atom_count": len(self.atoms),
            "dropped": self.dropped,
            "capacity": self.capacity,
            "by_category": self.category_counts(),
            "last_atoms": [a.sentence() for a in self.atoms[-5:]],
        }

    def to_trace(self) -> MeaningTrace:
        return MeaningTrace(atoms=list(self.atoms))
