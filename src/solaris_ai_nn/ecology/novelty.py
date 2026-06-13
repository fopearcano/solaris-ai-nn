"""Novelty -- bounded new structure that can become familiar.

The generator mints rare new stimulus patterns (and altered known ones),
but only up to a hard per-run cap: too much novelty is just noise. Every
novel pattern is traceable by id, and a novel pattern that recurs enough
is promoted to a stable (no-longer-novel) pattern -- novelty decaying into
familiarity is exactly the developmental signal we want to observe.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NoveltyGenerator:
    """Bounded, traceable, decaying novelty."""

    rng: Any = None
    max_novel_patterns: int = 50
    familiarity_threshold: int = 4  # recurrences before "familiar"
    novel_patterns: Dict[str, int] = field(default_factory=dict)
    stable_patterns: List[str] = field(default_factory=list)
    novelty_events: int = field(default=0, init=False)
    capped: int = field(default=0, init=False)

    def propose(self, step: int, altered_of: Optional[str] = None,
                ) -> Optional[Dict[str, Any]]:
        """A new (or altered) pattern, or None when capped."""
        if len(self.novel_patterns) >= self.max_novel_patterns:
            self.capped += 1
            return None
        index = len(self.novel_patterns) + 1
        pattern_id = (f"NOV_{index:04d}" if altered_of is None
                      else f"ALT_{altered_of}_{index:04d}")
        self.novel_patterns[pattern_id] = 0
        self.novelty_events += 1
        return {"pattern_id": pattern_id, "step": step,
                "altered_of": altered_of, "novelty_hint": 1.0}

    def observe_recurrence(self, pattern_id: str) -> bool:
        """Record a recurrence; returns True when it becomes familiar."""
        if pattern_id not in self.novel_patterns:
            return False
        self.novel_patterns[pattern_id] += 1
        if self.novel_patterns[pattern_id] >= self.familiarity_threshold:
            if pattern_id not in self.stable_patterns:
                self.stable_patterns.append(pattern_id)
            return True
        return False

    def is_stable(self, pattern_id: str) -> bool:
        return pattern_id in self.stable_patterns

    def snapshot(self) -> Dict[str, Any]:
        return {
            "novel_patterns": len(self.novel_patterns),
            "stable_patterns": len(self.stable_patterns),
            "novelty_events": self.novelty_events,
            "capped": self.capped,
            "max_novel_patterns": self.max_novel_patterns,
            "note": "novelty is bounded; repeated novelty becomes a "
                    "stable pattern",
        }
