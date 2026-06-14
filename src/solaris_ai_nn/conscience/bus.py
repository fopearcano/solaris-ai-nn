"""Conscience bus -- a local, in-process, low-compute message bus.

The :class:`ConscienceBus` carries canonical messages between modules in one
process. There is no network bus and no external message queue. Every
:class:`BusMessage` records its source module, timestamp, payload, and
evidence refs, and the bus can be replayed from JSONL for reproducibility.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class BusTopic:
    STIMULUS = "stimulus"
    PUSH = "push"
    DESIRE = "desire"
    ACTION_CANDIDATE = "action_candidate"
    ACTION_SUGGESTION = "action_suggestion"
    REACTION = "reaction"
    MEANING = "meaning"
    MEMORY_UPDATE = "memory_update"
    WORLD_MODEL_UPDATE = "world_model_update"
    PROTO_SYMBOL = "proto_symbol"
    HYPOTHESIS = "hypothesis"
    LOGOS_TENSION = "logos_tension"
    DEGRADATION = "degradation"
    REPAIR_ACTION = "repair_action"
    INNER_MAP_UPDATE = "inner_map_update"
    OPS_EVENT = "ops_event"
    GOVERNANCE_EVENT = "governance_event"
    SAFETY_EVENT = "safety_event"
    TELEMETRY = "telemetry"

    ALL = (STIMULUS, PUSH, DESIRE, ACTION_CANDIDATE, ACTION_SUGGESTION,
           REACTION, MEANING, MEMORY_UPDATE, WORLD_MODEL_UPDATE, PROTO_SYMBOL,
           HYPOTHESIS, LOGOS_TENSION, DEGRADATION, REPAIR_ACTION,
           INNER_MAP_UPDATE, OPS_EVENT, GOVERNANCE_EVENT, SAFETY_EVENT,
           TELEMETRY)


@dataclass
class BusMessage:
    """One canonical in-process message."""

    topic: str
    source_module: str
    payload: Dict[str, Any] = field(default_factory=dict)
    evidence_refs: List[str] = field(default_factory=list)
    message_id: str = field(default_factory=lambda: f"MSG_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)
    step: int = 0

    def __post_init__(self) -> None:
        if self.topic not in BusTopic.ALL:
            raise ValueError(f"unknown bus topic {self.topic!r}")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BusMessage":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class BusSubscription:
    """One subscriber callback for a topic."""

    topic: str
    callback: Callable[[BusMessage], None]
    subscriber: str = ""


@dataclass
class BusTrace:
    """A compact, replayable trace of bus traffic."""

    messages: List[BusMessage] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)

    def add(self, message: BusMessage) -> None:
        self.messages.append(message)
        self.messages = self.messages[-5000:]
        self.counts[message.topic] = self.counts.get(message.topic, 0) + 1

    def to_dict(self) -> Dict[str, Any]:
        return {"message_count": sum(self.counts.values()),
                "counts": dict(self.counts),
                "recent": [m.to_dict() for m in self.messages[-5:]]}


@dataclass
class ConscienceBus:
    """In-process publish/subscribe bus with JSONL replay."""

    state_dir: Optional[Union[str, Path]] = None
    write_log: bool = True
    trace: BusTrace = field(default_factory=BusTrace)
    _subscriptions: List[BusSubscription] = field(default_factory=list,
                                                 init=False)
    published_total: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.log_path = (Path(self.state_dir) / "conscience_bus.jsonl"
                         if self.state_dir else None)

    # -- pub/sub ------------------------------------------------------------------

    def subscribe(self, topic: str, callback: Callable[[BusMessage], None],
                  subscriber: str = "") -> BusSubscription:
        if topic not in BusTopic.ALL:
            raise ValueError(f"unknown bus topic {topic!r}")
        sub = BusSubscription(topic=topic, callback=callback,
                              subscriber=subscriber)
        self._subscriptions.append(sub)
        return sub

    def publish(self, topic: str, source_module: str,
                payload: Optional[Dict[str, Any]] = None,
                evidence_refs: Optional[List[str]] = None,
                step: int = 0) -> BusMessage:
        message = BusMessage(
            topic=topic, source_module=source_module,
            payload=dict(payload or {}),
            evidence_refs=list(evidence_refs or []), step=step)
        self.trace.add(message)
        self.published_total += 1
        for sub in self._subscriptions:
            if sub.topic == topic:
                try:
                    sub.callback(message)
                except Exception:  # a bad subscriber never breaks the bus
                    continue
        if self.write_log and self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(message.to_dict(), default=str) + "\n")
        return message

    # -- replay -------------------------------------------------------------------

    def replay_jsonl(self, path: Union[str, Path]) -> List[BusMessage]:
        out: List[BusMessage] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(BusMessage.from_dict(json.loads(line)))
        return out

    def message_count(self) -> int:
        return self.published_total

    def snapshot(self) -> Dict[str, Any]:
        return {
            "published_total": self.published_total,
            "subscriptions": len(self._subscriptions),
            "trace": self.trace.to_dict(),
            "log_path": str(self.log_path) if self.log_path else None,
        }
