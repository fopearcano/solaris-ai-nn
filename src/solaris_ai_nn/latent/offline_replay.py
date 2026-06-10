"""OfflineReplayEngine -- feed remembered windows back through a sandbox.

Replays operate on trace rows (the bridge's event/reaction records or the
runner's full signal rows) and run them through a *sandbox* bridge -- a
deterministic copy of the production bridge -- so the production substrate is
untouched unless mutation was explicitly permitted. All window selection is
seeded; the same trace and seed give the same windows.
"""

from __future__ import annotations

import copy
import random
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..bridges.neural_bridge import SolarisNeuralBridge
from ..signals import canonical as C
from ..utils.math import norm

REPLAY_STRATEGIES = ("recent", "high_valence", "high_novelty", "high_error",
                     "silence_window", "random_seeded")


def make_sandbox_bridge(bridge: SolarisNeuralBridge) -> SolarisNeuralBridge:
    """A deterministic, isolated copy of ``bridge`` for offline replay.

    Same configuration and seed, plus the current substrate state, readout
    weights, and habit table -- so the sandbox *starts where production is*
    but nothing it does flows back.
    """
    sandbox = SolarisNeuralBridge(
        action_labels=list(bridge.action_labels),
        encoder=copy.deepcopy(bridge.encoder),
        substrate_name=(bridge.substrate.name
                        if bridge.substrate.name != "esn" else "esn"),
        substrate_config=dict(bridge.substrate_config or {}),
        exploration=0.0,  # sandbox responses are greedy: deterministic
        seed=bridge.seed,
    )
    sandbox.substrate.set_state([float(x) for x in
                                 bridge.substrate.get_state()])
    sandbox.readout.weights = [row[:] for row in bridge.readout.weights]
    sandbox.habit.weights = dict(bridge.habit.weights)
    sandbox.habit.counts = dict(bridge.habit.counts)
    return sandbox


def row_to_stimulus(row: Dict[str, Any]) -> Optional[C.Stimulus]:
    """Rebuild a Stimulus from a trace row (full signal or lossy event)."""
    signal = row.get("signal")
    if isinstance(signal, dict):  # full replayable signal row
        return C.Stimulus(
            origin=str(signal.get("origin", "replay")),
            modality=str(signal.get("modality", "generic")),
            payload=signal.get("payload"),
            intensity=float(signal.get("intensity", 0.0) or 0.0),
            is_absence=bool(signal.get("is_absence", False)))
    if row.get("category") == "event":
        payload = row.get("payload")
        return C.Stimulus(
            origin="replay", modality="replayed",
            payload=None if payload in (None, "None") else payload,
            intensity=float(row.get("intensity", 0.5) or 0.5),
            is_absence=bool(row.get("is_absence", False)))
    return None


@dataclass
class OfflineReplayEngine:
    """Selects windows, replays them into sandboxes, measures the change."""

    seed: int = 0
    outcomes: List[Dict[str, Any]] = field(default_factory=list, init=False)

    # -- window selection ---------------------------------------------------------

    def select_windows(self, trace: Any, strategy: str = "recent",
                       window_size: int = 10,
                       count: int = 2) -> List[Dict[str, Any]]:
        """Pick ``count`` windows of rows from the trace, deterministically."""
        if strategy not in REPLAY_STRATEGIES:
            raise ValueError(f"unknown replay strategy {strategy!r}; "
                             f"choose from {REPLAY_STRATEGIES}")
        rows = self._rows(trace)
        if not rows:
            return []
        anchors = self._anchor_indices(rows, strategy, count)
        windows = []
        for i, anchor in enumerate(anchors):
            start = max(0, anchor - window_size + 1)
            window_rows = rows[start:anchor + 1]
            if not window_rows:
                continue
            windows.append({
                "window_id": f"{strategy}-{start}-{anchor}-"
                             f"{uuid.uuid4().hex[:6]}",
                "strategy": strategy,
                "start": start,
                "end": anchor,
                "rows": window_rows,
            })
        return windows

    @staticmethod
    def _rows(trace: Any) -> List[Dict[str, Any]]:
        if isinstance(trace, list):
            return list(trace)
        if hasattr(trace, "records"):  # TraceMemory
            return [r.to_row() for r in trace.records]
        raise TypeError("trace must be a TraceMemory or a list of row dicts")

    def _anchor_indices(self, rows: List[Dict[str, Any]], strategy: str,
                        count: int) -> List[int]:
        last = len(rows) - 1
        if strategy == "recent":
            step = max(1, (last + 1) // max(1, count))
            return sorted({last - i * step for i in range(count)
                           if last - i * step >= 0})
        if strategy == "random_seeded":
            rng = random.Random(self.seed)
            return sorted(rng.sample(range(len(rows)),
                                     min(count, len(rows))))

        def score(index: int) -> float:
            row = rows[index]
            if strategy == "high_valence":
                return abs(float(row.get("valence", 0.0) or 0.0))
            if strategy == "high_error":
                return abs(float(row.get("error", 0.0) or 0.0))
            if strategy == "high_novelty":
                novelty = row.get("novelty")
                if novelty is not None:
                    return float(novelty)
                return 1.0 if row.get("is_absence") else 0.0
            if strategy == "silence_window":
                return 1.0 if row.get("is_absence") else 0.0
            return 0.0

        ranked = sorted(range(len(rows)), key=lambda i: (-score(i), i))
        picked = [i for i in ranked[:count] if score(i) > 0.0]
        return sorted(picked) if picked else [last]

    # -- replay ---------------------------------------------------------------------

    def replay_window(self, window: Dict[str, Any],
                      bridge: SolarisNeuralBridge,
                      mutate: bool = False) -> Dict[str, Any]:
        """Replay one window into ``bridge``.

        ``mutate=False`` (default) processes stimuli only -- the substrate
        state moves (that is the point of replay) but nothing *learns*.
        ``mutate=True`` also applies recorded reactions so the readout/habit
        learn from the replay; callers use it on sandboxes freely, and on
        production only behind the latent-plasticity gate.
        """
        before = self.bridge_summary(bridge)
        replayed = 0
        for row in window.get("rows", []):
            stimulus = row_to_stimulus(row)
            if stimulus is not None:
                bridge.process(stimulus)
                replayed += 1
            if mutate and row.get("category") == "reaction":
                bridge.react(C.Reaction(
                    valence=float(row.get("valence", 0.0) or 0.0)))
            elif mutate and row.get("reaction") is not None:
                bridge.react(C.Reaction(
                    valence=float(row["reaction"])))
        after = self.bridge_summary(bridge)
        outcome = {
            "window_id": window.get("window_id"),
            "strategy": window.get("strategy"),
            "events_replayed": replayed,
            "mutate": mutate,
            "before": before,
            "after": after,
            "comparison": self.compare_before_after(before, after),
            "offline": True,
        }
        self.outcomes.append(outcome)
        self.outcomes = self.outcomes[-200:]
        return outcome

    @staticmethod
    def bridge_summary(bridge: SolarisNeuralBridge) -> Dict[str, Any]:
        suggestion = bridge.last_suggestion() or {}
        return {
            "state_norm": round(bridge.substrate_state_norm(), 6),
            "readout_weight_norm": round(
                bridge.readout.weight_magnitude(), 6),
            "habit_pathways": len(bridge.habit.weights),
            "suggested_action": suggestion.get("action"),
            "confidence": round(float(suggestion.get("confidence", 0.0)
                                      or 0.0), 6),
            "steps": bridge.telemetry.steps,
        }

    @staticmethod
    def compare_before_after(before: Dict[str, Any],
                             after: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "state_norm_drift": round(after["state_norm"]
                                      - before["state_norm"], 6),
            "readout_weight_delta": round(after["readout_weight_norm"]
                                          - before["readout_weight_norm"], 6),
            "habit_pathway_delta": after["habit_pathways"]
            - before["habit_pathways"],
            "suggestion_changed": after["suggested_action"]
            != before["suggested_action"],
            "confidence_delta": round(after["confidence"]
                                      - before["confidence"], 6),
        }

    def to_report(self) -> Dict[str, Any]:
        drifts = [abs(o["comparison"]["state_norm_drift"])
                  for o in self.outcomes]
        return {
            "replays": len(self.outcomes),
            "events_replayed": sum(o["events_replayed"]
                                   for o in self.outcomes),
            "mean_abs_state_drift": (round(sum(drifts) / len(drifts), 6)
                                     if drifts else 0.0),
            "suggestion_changes": sum(
                1 for o in self.outcomes
                if o["comparison"]["suggestion_changed"]),
            "mutating_replays": sum(1 for o in self.outcomes if o["mutate"]),
            "recent": self.outcomes[-5:],
            "offline": True,
        }
