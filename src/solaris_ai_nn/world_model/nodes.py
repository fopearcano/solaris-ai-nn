"""Graph nodes -- the symbols the world model is allowed to hold.

A node is a named, typed, counted observation: "this pattern / object /
action / context recurred". Confidence grows with observation count and is
capped well below certainty -- the graph stores observed structure, not
truths.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


class NodeType:
    STIMULUS_PATTERN = "stimulus_pattern"
    SIGNAL_TYPE = "signal_type"
    ENTITY = "entity"
    OBJECT = "object"
    PLACE = "place"
    ACTION = "action"
    REACTION = "reaction"
    HABIT = "habit"
    BOUNDARY = "boundary"
    CONTEXT = "context"
    STATE = "state"
    UNKNOWN = "unknown"
    SELF_REFERENCE = "self_reference"
    LATENT_SCHEMA = "latent_schema"
    # Ego / self-model (Prompt 18). Operational structure, not personhood.
    PERSPECTIVE_CONTEXT = "perspective_context"
    ACTION_AUTHORITY = "action_authority"
    ATTRIBUTION_SOURCE = "attribution_source"
    # Proto-language (Prompt 22). Internal operational symbols.
    PROTO_SYMBOL = "proto_symbol"

    ALL = (STIMULUS_PATTERN, SIGNAL_TYPE, ENTITY, OBJECT, PLACE, ACTION,
           REACTION, HABIT, BOUNDARY, CONTEXT, STATE, UNKNOWN,
           SELF_REFERENCE, LATENT_SCHEMA, PERSPECTIVE_CONTEXT,
           ACTION_AUTHORITY, ATTRIBUTION_SOURCE, PROTO_SYMBOL)


def slug(label: str) -> str:
    """A deterministic, readable identifier fragment from a label."""
    text = re.sub(r"[^a-z0-9]+", "_", str(label).lower()).strip("_")
    return text[:80] or "blank"


def node_id_for(node_type: str, label: str) -> str:
    """Deterministic node id: same type+label always maps to the same node."""
    return f"{node_type}:{slug(label)}"


def confidence_from_count(count: int) -> float:
    """Evidence-driven confidence, capped at 0.95 (never certainty)."""
    return round(min(0.95, count / (count + 2.0)), 4)


@dataclass
class GraphNode:
    """One observed symbol in the world model."""

    node_id: str
    type: str
    label: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    observation_count: int = 0
    confidence: float = 0.0
    source_modules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in NodeType.ALL:
            raise ValueError(f"unknown node type {self.type!r}")

    def observe(self, source_module: str = "",
                **metadata: Any) -> "GraphNode":
        """One more observation of this symbol."""
        self.observation_count += 1
        self.confidence = confidence_from_count(self.observation_count)
        self.updated_at = time.time()
        if source_module and source_module not in self.source_modules:
            self.source_modules.append(source_module)
            self.source_modules = self.source_modules[:10]
        for key, value in metadata.items():
            self.metadata[key] = value
        return self

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphNode":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})
