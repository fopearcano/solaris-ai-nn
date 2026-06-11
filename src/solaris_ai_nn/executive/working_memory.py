"""Working memory -- the executive's short-lived active context. Bounded."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkingMemoryItem:
    """One short-lived item of active context."""

    kind: str  # desire | candidate | inhibition | plan | prospection |
    # decision | constraint | mode | focus
    content: Dict[str, Any] = field(default_factory=dict)
    ttl_s: float = 120.0
    created_at: float = field(default_factory=time.time)

    def is_expired(self, now: Optional[float] = None) -> bool:
        return ((now if now is not None else time.time())
                - self.created_at) >= self.ttl_s

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class WorkingMemory:
    """Bounded, decaying store of what the executive is currently holding."""

    max_items: int = 50
    items: List[WorkingMemoryItem] = field(default_factory=list)
    focus: Optional[Dict[str, Any]] = None
    mode: str = "arbitrated"
    constraints: List[str] = field(default_factory=list)

    def add(self, kind: str, content: Dict[str, Any],
            ttl_s: float = 120.0) -> WorkingMemoryItem:
        item = WorkingMemoryItem(kind=kind, content=dict(content),
                                 ttl_s=ttl_s)
        self.items.append(item)
        self.expire()
        self.items = self.items[-self.max_items:]
        return item

    def expire(self, now: Optional[float] = None) -> int:
        before = len(self.items)
        self.items = [i for i in self.items if not i.is_expired(now)]
        return before - len(self.items)

    def recent(self, kind: Optional[str] = None,
               limit: int = 10) -> List[WorkingMemoryItem]:
        items = [i for i in self.items
                 if kind is None or i.kind == kind]
        return items[-limit:]

    def set_focus(self, focus: Dict[str, Any]) -> None:
        self.focus = dict(focus)

    def set_mode(self, mode: str) -> None:
        self.mode = mode

    def set_constraints(self, constraints: List[str]) -> None:
        self.constraints = list(constraints)[:20]

    def __len__(self) -> int:
        return len(self.items)

    def snapshot(self) -> Dict[str, Any]:
        self.expire()
        counts: Dict[str, int] = {}
        for item in self.items:
            counts[item.kind] = counts.get(item.kind, 0) + 1
        return {
            "items": len(self.items),
            "counts_by_kind": dict(sorted(counts.items())),
            "focus": self.focus,
            "mode": self.mode,
            "constraints": list(self.constraints),
            "recent": [i.to_dict() for i in self.items[-5:]],
        }
