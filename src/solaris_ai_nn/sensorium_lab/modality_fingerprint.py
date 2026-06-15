"""Modality fingerprint -- what each modality actually contributed.

A :class:`ModalityFingerprint` records, per modality, how much structure it
produced: events, receptor adaptation, baseline shifts, absences, rhythms,
invariants, proto-symbols, world nodes, hypotheses, attention shifts, and rough
prediction/compression/contamination contributions. A modality with many events
but no structural effect is reported honestly (``structurally_weak``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ModalityFingerprint:
    """One modality's structural contribution under a sensorium arm."""

    modality: str
    event_count: int = 0
    receptor_adaptation_count: int = 0
    baseline_shifts: int = 0
    absences: int = 0
    rhythms: int = 0
    invariants: int = 0
    proto_symbols: int = 0
    world_nodes: int = 0
    hypotheses: int = 0
    attention_shifts: int = 0
    prediction_contribution: float = 0.0
    compression_contribution: float = 0.0
    contamination_contribution: float = 0.0
    limitations: List[str] = field(default_factory=list)

    @property
    def structural_effect(self) -> int:
        return (self.baseline_shifts + self.absences + self.rhythms
                + self.invariants + self.proto_symbols)

    @property
    def structurally_weak(self) -> bool:
        # Many events but essentially no structure formed.
        return self.event_count >= 4 and self.structural_effect == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "modality": self.modality,
            "event_count": self.event_count,
            "receptor_adaptation_count": self.receptor_adaptation_count,
            "baseline_shifts": self.baseline_shifts,
            "absences": self.absences,
            "rhythms": self.rhythms,
            "invariants": self.invariants,
            "proto_symbols": self.proto_symbols,
            "world_nodes": self.world_nodes,
            "hypotheses": self.hypotheses,
            "attention_shifts": self.attention_shifts,
            "prediction_contribution": self.prediction_contribution,
            "compression_contribution": self.compression_contribution,
            "contamination_contribution": self.contamination_contribution,
            "structural_effect": self.structural_effect,
            "structurally_weak": self.structurally_weak,
            "limitations": list(self.limitations),
        }


@dataclass
class ModalityFingerprintBuilder:
    """Builds per-modality fingerprints from a completed runtime."""

    def build(self, runtime: Any) -> List[ModalityFingerprint]:
        rt = runtime
        fingerprints: Dict[str, ModalityFingerprint] = {}

        def fp(modality: str) -> ModalityFingerprint:
            if modality not in fingerprints:
                fingerprints[modality] = ModalityFingerprint(modality=modality)
            return fingerprints[modality]

        for receptor in rt.receptors.values():
            f = fp(receptor.modality)
            f.event_count += receptor.event_count
            f.receptor_adaptation_count += receptor.adaptation_count
        for shift in rt.baseline_shifts:
            fp(shift.get("modality", "unknown")).baseline_shifts += 1
        for ev in rt.absence.events:
            fp(ev.modality).absences += 1
        for sig in rt.rhythm.signatures.values():
            fp(sig.modality).rhythms += 1
        for cand in rt.invariants.candidates.values():
            fp(cand.modality).invariants += 1
        for proto in rt.proto_symbol_candidates:
            f = fp(proto.get("modality", "unknown"))
            f.proto_symbols += 1
            if proto.get("human_label_contaminated"):
                f.contamination_contribution += 1.0
        for struct in rt.world_model_structures:
            if struct.get("kind") == "modality_source":
                fp(struct.get("modality", "unknown")).world_nodes += 1
        for hyp in rt.hypotheses:
            fp(hyp.get("modality", "unknown")).hypotheses += 1
        for shift in rt.attention.history:
            target = str(shift.target)
            for modality in fingerprints:
                if modality in target:
                    fingerprints[modality].attention_shifts += 1

        for f in fingerprints.values():
            # Rough proxies: invariants/rhythms aid prediction; stable symbols
            # aid compression. These are coarse, not calibrated quantities.
            f.prediction_contribution = round(
                min(1.0, (f.invariants + f.rhythms) / 5.0), 4)
            f.compression_contribution = round(
                min(1.0, f.proto_symbols / 3.0), 4)
            if f.structurally_weak:
                f.limitations.append(
                    "many events but no structural effect: this modality did "
                    "not shape the system under this sensorium")
        return list(fingerprints.values())
