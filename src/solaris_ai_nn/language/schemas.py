"""Internal language schemas -- structured meaning, not chat.

These dataclasses are the vocabulary-carrying containers of the language layer:
meaning atoms (subject-predicate-value statements grounded in runtime state),
meaning/causal traces, explanations, reports, and query results. Everything
serializes to plain dicts. Nothing here generates free prose from hidden
assumptions, and nothing claims consciousness -- an atom is a record, an
explanation is a rendering of records.
"""

from __future__ import annotations

import itertools
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_ids = itertools.count(1)


def _next_id(prefix: str) -> str:
    return f"{prefix}-{next(_ids)}"


@dataclass
class LanguageEvent:
    """A raw, timestamped happening the language layer was told about."""

    category: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: _next_id("evt"))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "timestamp": self.timestamp,
                "category": self.category, "description": self.description,
                "data": dict(self.data)}


@dataclass
class MeaningAtom:
    """One grounded statement: subject -- predicate -- value.

    Examples: ("Stimulus", "received", "intensity=0.7"),
    ("reservoir_state", "updated", "norm=4.72"),
    ("habit:near:reward->touch_object", "reinforced", "0.85").
    """

    category: str
    subject: str
    predicate: str
    value: Any = None
    confidence: float = 1.0
    source_module: str = ""
    source_signal_id: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    atom_id: str = field(default_factory=lambda: _next_id("atom"))
    timestamp: float = field(default_factory=time.time)

    def sentence(self) -> str:
        """Deterministic one-line rendering of the atom."""
        value = "" if self.value is None else f" {self.value}"
        return f"[{self.category}] {self.subject} {self.predicate}{value}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "atom_id": self.atom_id, "timestamp": self.timestamp,
            "category": self.category, "subject": self.subject,
            "predicate": self.predicate, "value": self.value,
            "confidence": self.confidence, "source_module": self.source_module,
            "source_signal_id": self.source_signal_id,
            "metadata": dict(self.metadata),
        }


@dataclass
class MeaningTrace:
    """An ordered, bounded sequence of meaning atoms."""

    atoms: List[MeaningAtom] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"created_at": self.created_at, "atom_count": len(self.atoms),
                "atoms": [a.to_dict() for a in self.atoms]}


@dataclass
class CausalLink:
    """A (possibly heuristic) directed relation between two happenings.

    ``confidence < 1.0`` marks heuristic links; the relation word must hedge
    accordingly ("preceded", "was_associated_with", "influenced") unless the
    connection is directly coded in the system.
    """

    source: str
    target: str
    relation: str
    confidence: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def sentence(self) -> str:
        hedge = "" if self.confidence >= 0.99 else f" (confidence {self.confidence:.2f})"
        return f"{self.source} {self.relation.replace('_', ' ')} {self.target}{hedge}"

    def to_dict(self) -> Dict[str, Any]:
        return {"source": self.source, "target": self.target,
                "relation": self.relation, "confidence": self.confidence,
                "metadata": dict(self.metadata)}


@dataclass
class CausalTrace:
    """An approximate causal chain built from recorded events."""

    links: List[CausalLink] = field(default_factory=list)
    chain_id: str = field(default_factory=lambda: _next_id("chain"))
    note: str = ("links are heuristic reconstructions from recorded traces; "
                 "confidence below 1.0 means association, not proven causation")

    def to_dict(self) -> Dict[str, Any]:
        return {"chain_id": self.chain_id, "note": self.note,
                "links": [l.to_dict() for l in self.links]}


@dataclass
class Explanation:
    """A grounded explanation: text + the concrete fields it rests on."""

    topic: str
    text: str
    grounded_in: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    confidence: float = 1.0
    atoms: List[MeaningAtom] = field(default_factory=list)
    explanation_id: str = field(default_factory=lambda: _next_id("expl"))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "explanation_id": self.explanation_id, "timestamp": self.timestamp,
            "topic": self.topic, "text": self.text,
            "grounded_in": list(self.grounded_in),
            "unknowns": list(self.unknowns), "confidence": self.confidence,
            "atoms": [a.to_dict() for a in self.atoms],
        }


@dataclass
class ExplanationContext:
    """Everything an explanation may ground itself in. All fields optional;
    explanations must name what is missing instead of inventing it."""

    last_signal: Optional[Dict[str, Any]] = None
    bridge: Optional[Dict[str, Any]] = None
    telemetry: Optional[Dict[str, Any]] = None
    inner_map: Optional[Dict[str, Any]] = None
    embodiment: Optional[Dict[str, Any]] = None
    plasticity: Optional[Dict[str, Any]] = None
    habits: List[Dict[str, Any]] = field(default_factory=list)
    last_result: Optional[Dict[str, Any]] = None
    pruning: Optional[Dict[str, Any]] = None
    continuity: Optional[Dict[str, Any]] = None
    trace_summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class SystemUtterance:
    """One rendered statement from the system about itself (grounded)."""

    kind: str
    text: str
    grounded: bool = True
    utterance_id: str = field(default_factory=lambda: _next_id("utt"))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"utterance_id": self.utterance_id, "timestamp": self.timestamp,
                "kind": self.kind, "text": self.text, "grounded": self.grounded}


@dataclass
class ExperimentReport:
    """Structured experiment/session report (rendered by `reporting.py`)."""

    title: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: Dict[str, Any] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "created_at": self.created_at,
                "metadata": dict(self.metadata), "sections": dict(self.sections),
                "limitations": list(self.limitations)}


@dataclass
class QueryResult:
    """Answer to one deterministic internal query."""

    query: str
    answered: bool
    text: str
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {"query": self.query, "answered": self.answered,
                "text": self.text, "data": dict(self.data),
                "confidence": self.confidence}
