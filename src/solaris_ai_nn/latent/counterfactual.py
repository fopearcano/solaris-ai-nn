"""CounterfactualGenerator -- safe "what if" variants of remembered windows.

A counterfactual is a deterministic, seeded transformation of a trace window:
invert the reaction valence, drop a stimulus, lengthen the silence, change
the Logos fracture, swap reward/danger markers, suppress absence stimuli, or
amplify novelty. Every generated counterfactual is labelled
``simulated=True, offline=True`` and is only ever replayed into sandboxes --
never into real memory, sidecar channels, or action paths.
"""

from __future__ import annotations

import copy
import random
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List

from .safety import LatentSafetyReport, LatentSafetyValidator

COUNTERFACTUAL_KINDS = (
    "invert_valence", "remove_stimulus", "increase_silence",
    "change_fracture", "swap_reward_danger", "suppress_absence",
    "amplify_novelty",
)

_REWARD_MARKERS = {"reward": "danger", "food": "danger",
                   "reward_nearby": "danger_nearby"}


@dataclass
class CounterfactualGenerator:
    """Generates labelled, validated counterfactual trace windows."""

    safety: LatentSafetyValidator = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.safety is None:
            self.safety = LatentSafetyValidator()

    def generate(self, trace_window: Dict[str, Any], kind: str,
                 seed: int = 0) -> Dict[str, Any]:
        """One altered copy of ``trace_window``; deterministic per seed."""
        if kind not in COUNTERFACTUAL_KINDS:
            raise ValueError(f"unknown counterfactual kind {kind!r}; "
                             f"choose from {COUNTERFACTUAL_KINDS}")
        rows = copy.deepcopy(trace_window.get("rows", []))
        rng = random.Random(seed)
        transform = getattr(self, f"_{kind}")
        altered, change_note = transform(rows, rng)
        counterfactual = {
            "counterfactual_id": uuid.uuid4().hex[:12],
            "kind": kind,
            "seed": seed,
            "original_window_id": trace_window.get("window_id"),
            "rows": altered,
            "change_note": change_note,
            "simulated": True,
            "offline": True,
        }
        return counterfactual

    def describe(self, counterfactual: Dict[str, Any]) -> str:
        """A grounded one-liner; always marked as offline simulation."""
        return (f"offline simulated counterfactual "
                f"({counterfactual.get('kind')}): "
                f"{counterfactual.get('change_note', 'no change recorded')} "
                f"[window {counterfactual.get('original_window_id')}; "
                "not a real observation]")

    def validate(self, counterfactual: Dict[str, Any]) -> LatentSafetyReport:
        return self.safety.validate_counterfactual(counterfactual)

    # -- transformations (each returns (rows, change_note)) ---------------------

    @staticmethod
    def _invert_valence(rows: List[Dict[str, Any]], rng: random.Random):
        flipped = 0
        for row in rows:
            if row.get("category") == "reaction" or row.get(
                    "valence") is not None:
                value = float(row.get("valence", 0.0) or 0.0)
                row["valence"] = -value
                flipped += 1
            if row.get("reaction") is not None:
                row["reaction"] = -float(row["reaction"])
                flipped += 1
        return rows, f"inverted the valence of {flipped} reaction value(s)"

    @staticmethod
    def _remove_stimulus(rows: List[Dict[str, Any]], rng: random.Random):
        stimulus_indices = [i for i, r in enumerate(rows)
                            if r.get("category") in ("event", "signal")]
        if not stimulus_indices:
            return rows, "no stimulus to remove"
        index = rng.choice(stimulus_indices)
        removed = rows.pop(index)
        return rows, (f"removed one stimulus at window position {index} "
                      f"(payload {str(removed.get('payload'))[:30]!r})")

    @staticmethod
    def _increase_silence(rows: List[Dict[str, Any]], rng: random.Random):
        extra = 3
        last_step = int(rows[-1].get("step", 0)) if rows else 0
        for i in range(extra):
            rows.append({"category": "event", "kind": "Stimulus",
                         "step": last_step + i + 1, "payload": None,
                         "is_absence": True, "intensity": 0.3 + 0.1 * i})
        return rows, f"appended {extra} extra absence stimuli (longer silence)"

    @staticmethod
    def _change_fracture(rows: List[Dict[str, Any]], rng: random.Random):
        first_step = int(rows[0].get("step", 0)) if rows else 0
        rows.insert(0, {"category": "signal", "step": first_step,
                        "signal": {"kind": "LogosTension", "origin": "dream",
                                   "division": 0.9, "union": 0.1},
                        "fracture": 0.8})
        return rows, "prepended a high-fracture LogosTension (0.8)"

    @staticmethod
    def _swap_reward_danger(rows: List[Dict[str, Any]], rng: random.Random):
        swapped = 0
        for row in rows:
            payload = row.get("payload")
            if isinstance(payload, str):
                lowered = payload.lower()
                for marker, replacement in _REWARD_MARKERS.items():
                    if marker in lowered:
                        row["payload"] = lowered.replace(marker, replacement)
                        swapped += 1
                        break
        return rows, f"swapped reward->danger markers in {swapped} payload(s)"

    @staticmethod
    def _suppress_absence(rows: List[Dict[str, Any]], rng: random.Random):
        kept = [r for r in rows if not r.get("is_absence")]
        removed = len(rows) - len(kept)
        rows[:] = kept
        return rows, f"suppressed {removed} absence stimul{'us' if removed == 1 else 'i'}"

    @staticmethod
    def _amplify_novelty(rows: List[Dict[str, Any]], rng: random.Random):
        bumped = 0
        for row in rows:
            if row.get("category") in ("event", "signal"):
                row["intensity"] = min(1.0, float(
                    row.get("intensity", 0.5) or 0.5) * 1.5)
                if row.get("novelty") is not None:
                    row["novelty"] = min(1.0, float(row["novelty"]) + 0.3)
                bumped += 1
        return rows, f"amplified intensity/novelty on {bumped} row(s)"
