"""GridWorld -- a minimal, bounded, deterministic 2D world.

A rectangular grid with walls at its edges and a handful of object kinds
(signal sources, obstacles, reward/danger/unknown markers). Movement respects
boundaries and obstacles; touching interacts with markers; everything is
deterministic per seed. ASCII rendering only -- no graphics, no real world.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .base import Environment, Position

SIGNAL = "signal_source"
OBSTACLE = "obstacle"
REWARD = "reward_marker"
DANGER = "danger_marker"
UNKNOWN = "unknown_marker"

OBJECT_KINDS = (SIGNAL, OBSTACLE, REWARD, DANGER, UNKNOWN)
SYMBOLS = {SIGNAL: "S", OBSTACLE: "O", REWARD: "R", DANGER: "D", UNKNOWN: "?"}

_DELTAS = {
    "move_north": (0, -1),
    "move_south": (0, 1),
    "move_east": (1, 0),
    "move_west": (-1, 0),
}

DEFAULT_COUNTS = {SIGNAL: 1, OBSTACLE: 3, REWARD: 2, DANGER: 2, UNKNOWN: 1}


def manhattan(a: Position, b: Position) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


@dataclass
class GridWorld(Environment):
    """Bounded grid with deterministic object placement.

    Args:
        width / height: Interior size (walls surround the grid implicitly).
        seed: Deterministic layout seed.
        object_counts: How many of each object kind to place.
        sense_range: Manhattan radius within which objects are "sensed".
    """

    width: int = 9
    height: int = 7
    seed: int = 0
    object_counts: Dict[str, int] = field(default_factory=lambda: dict(DEFAULT_COUNTS))
    sense_range: int = 3

    agent_pos: Position = field(default=(0, 0), init=False)
    objects: Dict[Position, str] = field(default_factory=dict, init=False)
    ticks: int = field(default=0, init=False)
    consumed: Dict[str, int] = field(default_factory=dict, init=False)
    pings: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.width < 3 or self.height < 3:
            raise ValueError("grid must be at least 3x3")
        self.reset(self.seed)

    # -- lifecycle ------------------------------------------------------------

    def reset(self, seed: Optional[int] = None) -> None:
        """Re-place agent + objects deterministically for ``seed``."""
        if seed is not None:
            self.seed = seed
        rng = random.Random(self.seed)
        self.agent_pos = (self.width // 2, self.height // 2)
        self.objects = {}
        self.ticks = 0
        self.consumed = {}
        self.pings = 0
        cells = [(x, y) for x in range(self.width) for y in range(self.height)
                 if (x, y) != self.agent_pos]
        rng.shuffle(cells)
        idx = 0
        for kind in OBJECT_KINDS:
            for _ in range(int(self.object_counts.get(kind, 0))):
                if idx >= len(cells):
                    break
                self.objects[cells[idx]] = kind
                idx += 1

    # -- geometry -------------------------------------------------------------

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def object_at(self, pos: Position) -> Optional[str]:
        return self.objects.get(pos)

    def wall_distance(self, pos: Optional[Position] = None) -> int:
        x, y = pos or self.agent_pos
        return min(x, y, self.width - 1 - x, self.height - 1 - y)

    def nearest(self, kind: Optional[str] = None,
                pos: Optional[Position] = None) -> Optional[Tuple[str, Position, int]]:
        """Nearest object (optionally of one kind): (kind, position, distance)."""
        origin = pos or self.agent_pos
        best = None
        for opos, okind in self.objects.items():
            if kind is not None and okind != kind:
                continue
            d = manhattan(origin, opos)
            if best is None or d < best[2]:
                best = (okind, opos, d)
        return best

    def _step_toward(self, target: Position, away: bool = False) -> Position:
        x, y = self.agent_pos
        tx, ty = target
        dx = (1 if tx > x else -1 if tx < x else 0)
        dy = (1 if ty > y else -1 if ty < y else 0)
        if away:
            dx, dy = -dx, -dy
        # Prefer the axis with the larger gap; fall back to the other.
        first = (x + dx, y) if abs(tx - x) >= abs(ty - y) else (x, y + dy)
        second = (x, y + dy) if first[1] == y else (x + dx, y)
        for cand in (first, second):
            if cand != self.agent_pos and self.in_bounds(cand) \
                    and self.object_at(cand) != OBSTACLE:
                return cand
        return self.agent_pos

    # -- dynamics -------------------------------------------------------------

    def step(self, action: str) -> Dict[str, Any]:
        """Apply one simulated action; returns what happened."""
        self.ticks += 1
        before = self.agent_pos
        events: List[str] = []
        blocked: Optional[str] = None
        changed = False

        if action in _DELTAS:
            dx, dy = _DELTAS[action]
            target = (before[0] + dx, before[1] + dy)
            if not self.in_bounds(target):
                blocked = "wall"
            elif self.object_at(target) == OBSTACLE:
                blocked = "obstacle"
            else:
                self.agent_pos = target
        elif action in ("approach_signal", "avoid_signal"):
            nearest_signal = self.nearest(SIGNAL)
            if nearest_signal is None:
                blocked = "no_signal"
            else:
                new = self._step_toward(nearest_signal[1],
                                        away=(action == "avoid_signal"))
                if new == before:
                    blocked = "wall" if self.wall_distance() == 0 else "obstacle"
                else:
                    self.agent_pos = new
        elif action == "touch_object":
            target = self._adjacent_object()
            if target is None:
                events.append("nothing_to_touch")
            else:
                tpos, tkind = target
                events.append(f"touched:{tkind}")
                if tkind in (REWARD, UNKNOWN):
                    del self.objects[tpos]  # consumed / resolved
                    self.consumed[tkind] = self.consumed.get(tkind, 0) + 1
                    changed = True
        elif action == "emit_ping":
            self.pings += 1
            near = self.nearest()
            events.append(f"ping_echo:{near[0]}" if near else "ping_echo:none")
        elif action == "look":
            visible = sorted({k for p, k in self.objects.items()
                              if manhattan(self.agent_pos, p) <= self.sense_range})
            events.append("saw:" + (",".join(visible) if visible else "nothing"))
        elif action == "rest":
            events.append("rested")
        else:
            blocked = "unknown_action"

        on_object = self.object_at(self.agent_pos)
        if on_object is not None:
            events.append(f"on:{on_object}")

        return {
            "action": action,
            "position_before": before,
            "position_after": self.agent_pos,
            "blocked": blocked,
            "events": events,
            "environment_changed": changed,
        }

    def _adjacent_object(self) -> Optional[Tuple[Position, str]]:
        x, y = self.agent_pos
        for pos in ((x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            kind = self.object_at(pos)
            if kind is not None and kind != OBSTACLE:
                return pos, kind
        return None

    # -- sensing ----------------------------------------------------------------

    def sense(self, position: Optional[Position] = None) -> Dict[str, Any]:
        """Raw sensory summary around ``position`` (defaults to the agent)."""
        pos = position or self.agent_pos
        nearby = []
        for opos, okind in self.objects.items():
            d = manhattan(pos, opos)
            if d <= self.sense_range:
                nearby.append({"kind": okind, "distance": d})
        nearby.sort(key=lambda o: o["distance"])
        return {
            "position": pos,
            "nearby": nearby,
            "wall_distance": self.wall_distance(pos),
            "on_object": self.object_at(pos),
            "any_signal": bool(nearby),
        }

    # -- inspection ---------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            "type": "GridWorld",
            "width": self.width, "height": self.height, "seed": self.seed,
            "agent_pos": list(self.agent_pos),
            "objects": [{"pos": list(p), "kind": k} for p, k in sorted(self.objects.items())],
            "ticks": self.ticks,
            "consumed": dict(self.consumed),
            "pings": self.pings,
        }

    def to_ascii(self) -> str:
        rows = ["#" * (self.width + 2)]
        for y in range(self.height):
            row = "#"
            for x in range(self.width):
                if (x, y) == self.agent_pos:
                    row += "A"
                else:
                    row += SYMBOLS.get(self.objects.get((x, y), ""), ".")
            rows.append(row + "#")
        rows.append("#" * (self.width + 2))
        return "\n".join(rows)
