"""Environmental grounding -- operational association, not understanding.

The :class:`SensoryGroundingEngine` associates normalized sensory events with
internal structures: world-model node candidates, proto-symbol candidates,
Mysterium (novelty) events, active-perception targets, hypothesis seeds, and
developmental-milestone hints. Grounding is *operational association* with
preserved provenance -- textual labels from input are never truth labels, and
proto-symbols are still generated internally, not copied from input words.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EnvironmentalGroundingRecord:
    """One operational association between a sensory event and internals."""

    record_id: str
    source_id: str
    modality: str
    world_model_node_candidate: Optional[str] = None
    proto_symbol_candidate: Optional[str] = None
    mysterium_event: bool = False
    active_perception_target: Optional[str] = None
    hypothesis_seed: Optional[str] = None
    milestone_hint: Optional[str] = None
    provenance_refs: List[str] = field(default_factory=list)
    note: str = "operational association, not human understanding"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoryGroundingEngine:
    """Builds grounding records and tracks recurrence for proto-candidates."""

    proto_symbol_threshold: int = 3
    records: List[EnvironmentalGroundingRecord] = field(default_factory=list,
                                                        init=False)
    _recurrence: Dict[str, int] = field(default_factory=dict, init=False)
    proto_symbol_candidates: List[str] = field(default_factory=list,
                                               init=False)

    def ground(self, event: Any) -> EnvironmentalGroundingRecord:
        e = event.to_dict() if hasattr(event, "to_dict") else dict(event)
        source_id = e.get("source_id", "unknown")
        modality = e.get("modality", "unknown")
        recurrence_key = e.get("recurrence_key", "")
        novelty = float(e.get("novelty", 0.0) or 0.0)
        is_absence = bool(e.get("is_absence"))

        seen = self._recurrence.get(recurrence_key, 0) + 1 \
            if recurrence_key else 0
        if recurrence_key:
            self._recurrence[recurrence_key] = seen

        # A repeated environmental pattern becomes a proto-symbol *candidate*
        # (internally generated; the input text is not the symbol).
        proto_candidate = None
        if seen >= self.proto_symbol_threshold:
            proto_candidate = f"env_sym::{source_id}::{modality}::{seen}"
            if proto_candidate not in self.proto_symbol_candidates:
                self.proto_symbol_candidates.append(proto_candidate)

        record = EnvironmentalGroundingRecord(
            record_id=f"GND_{uuid.uuid4().hex[:10]}",
            source_id=source_id, modality=modality,
            world_model_node_candidate=f"env_source::{source_id}",
            proto_symbol_candidate=proto_candidate,
            mysterium_event=novelty >= 0.8,
            active_perception_target=(f"source::{source_id}"
                                      if novelty >= 0.5 else None),
            hypothesis_seed=(f"absence::{source_id}" if is_absence
                             else (f"recurring::{recurrence_key}"
                                   if seen >= self.proto_symbol_threshold
                                   else None)),
            milestone_hint=("first_environmental_symbol"
                            if proto_candidate and
                            len(self.proto_symbol_candidates) == 1 else None),
            provenance_refs=list(e.get("provenance_refs", [])))
        self.records.append(record)
        self.records = self.records[-2000:]
        return record

    def context(self) -> Dict[str, Any]:
        """A context dict for world-model / proto-language / hypothesis layers."""
        return {
            "sensory_world_model_nodes": sorted({
                r.world_model_node_candidate for r in self.records
                if r.world_model_node_candidate}),
            "sensory_proto_symbol_candidates": list(
                self.proto_symbol_candidates),
            "sensory_hypothesis_seeds": sorted({
                r.hypothesis_seed for r in self.records if r.hypothesis_seed}),
            "sensory_mysterium_events": sum(1 for r in self.records
                                            if r.mysterium_event),
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "grounding_count": len(self.records),
            "proto_symbol_candidate_count": len(self.proto_symbol_candidates),
            "world_model_node_count": len({
                r.world_model_node_candidate for r in self.records
                if r.world_model_node_candidate}),
            "hypothesis_seed_count": len({
                r.hypothesis_seed for r in self.records if r.hypothesis_seed}),
            "recent": [r.to_dict() for r in self.records[-8:]],
        }
