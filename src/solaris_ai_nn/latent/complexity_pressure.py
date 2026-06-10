"""ComplexityPressureMonitor -- too inert, too chaotic, or stuck in between.

Reads recent behaviour (actions, signals, substrate metrics, habit and
pruning statistics) and produces scores plus one bounded suggestion:
exploration, rest, consolidation, replay, or a flag. Suggestions are
internal recommendations only -- nothing here forces an action, and any
proposed parameter change still goes through governance + plasticity safety.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ComplexityDecision:
    NO_ACTION = "no_action"
    SUGGEST_EXPLORATION = "suggest_exploration"
    SUGGEST_REST = "suggest_rest"
    SUGGEST_CONSOLIDATION = "suggest_consolidation"
    SUGGEST_REPLAY = "suggest_replay"
    FLAG_INERTIA = "flag_inertia"
    FLAG_RUNAWAY = "flag_runaway"

    ALL = (NO_ACTION, SUGGEST_EXPLORATION, SUGGEST_REST,
           SUGGEST_CONSOLIDATION, SUGGEST_REPLAY, FLAG_INERTIA, FLAG_RUNAWAY)


@dataclass
class ComplexityReading:
    """Scores plus one decision (a suggestion, never a command)."""

    decision: str = ComplexityDecision.NO_ACTION
    reasons: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ComplexityPressureMonitor:
    """Detects inertia / chaos / deadlock from recent behaviour."""

    runaway_norm: float = 50.0
    inert_norm: float = 0.01
    history: List[Dict[str, Any]] = field(default_factory=list, init=False)

    def evaluate(self, context: Optional[Dict[str, Any]] = None,
                 ) -> ComplexityReading:
        ctx = context or {}
        actions: List[str] = list(ctx.get("recent_actions") or [])
        signals: List[str] = list(ctx.get("recent_signal_kinds") or [])
        state_norm = float(ctx.get("state_norm", 0.0) or 0.0)
        activity = float(ctx.get("activity_rate", 0.0) or 0.0)
        drift = float(ctx.get("state_drift", 0.0) or 0.0)
        habit_weights: Dict[Any, float] = dict(ctx.get("habit_weights") or {})
        pruned = int(ctx.get("pruned_pathways", 0) or 0)
        total_pathways = int(ctx.get("total_pathways", 0) or 0)

        action_diversity = (len(set(actions)) / len(actions)) if actions else 0.0
        signal_diversity = (len(set(signals)) / len(signals)) if signals else 0.0
        repeated_loop = self._repeated_loop_score(actions)

        inertia = 0.0
        if state_norm <= self.inert_norm and activity <= 0.01:
            inertia = 1.0
        elif activity < 0.1 and drift < 0.001:
            inertia = 0.6
        chaos = min(1.0, state_norm / self.runaway_norm) if state_norm > 0 \
            else 0.0
        if drift > 5.0:
            chaos = max(chaos, 0.8)
        balance = (1.0 if (actions and action_diversity <= 0.34
                           and repeated_loop >= 0.8 and inertia < 0.5)
                   else 0.0)

        habit_dom = 0.0
        if habit_weights:
            total = sum(abs(w) for w in habit_weights.values()) or 1e-9
            habit_dom = max(abs(w) for w in habit_weights.values()) / total
        pruning_dom = (pruned / max(1, pruned + total_pathways))

        scores = {
            "inertia": round(inertia, 4),
            "chaos": round(chaos, 4),
            "balance_deadlock": round(balance, 4),
            "repeated_loop": round(repeated_loop, 4),
            "action_diversity": round(action_diversity, 4),
            "signal_diversity": round(signal_diversity, 4),
            "substrate_drift": round(drift, 6),
            "habit_overdominance": round(habit_dom, 4),
            "pruning_overdominance": round(pruning_dom, 4),
        }
        decision, reasons = self._decide(scores)
        reading = ComplexityReading(decision=decision, reasons=reasons,
                                    scores=scores)
        self.history.append(reading.to_dict())
        self.history = self.history[-100:]
        return reading

    @staticmethod
    def _repeated_loop_score(actions: List[str]) -> float:
        """How much of the recent action stream is one repeating short loop."""
        if len(actions) < 6:
            return 0.0
        best = 0.0
        for k in (1, 2, 3):
            pattern = tuple(actions[-k:])
            repeats = 0
            i = len(actions) - k
            while i - k >= 0 and tuple(actions[i - k:i]) == pattern:
                repeats += 1
                i -= k
            covered = (repeats + 1) * k
            best = max(best, covered / len(actions))
        return min(1.0, best)

    @staticmethod
    def _decide(scores: Dict[str, float]) -> "tuple[str, List[str]]":
        D = ComplexityDecision
        if scores["chaos"] >= 0.9:
            return D.FLAG_RUNAWAY, [
                f"substrate activity is runaway (chaos {scores['chaos']})"]
        if scores["inertia"] >= 0.9:
            return D.FLAG_INERTIA, [
                "the substrate is inert (no activity, no drift)"]
        if scores["chaos"] >= 0.6:
            return D.SUGGEST_REST, [
                f"activity is high (chaos {scores['chaos']}); a sleep cycle "
                "would let it settle"]
        if scores["balance_deadlock"] >= 1.0 \
                or scores["repeated_loop"] >= 0.8:
            return D.SUGGEST_EXPLORATION, [
                "behaviour is locked in a short repeating loop; exploration "
                "would break the deadlock"]
        if scores["habit_overdominance"] >= 0.8:
            return D.SUGGEST_REPLAY, [
                "one habit dominates; offline replay would re-test it "
                "against remembered evidence"]
        if scores["inertia"] >= 0.5:
            return D.SUGGEST_CONSOLIDATION, [
                "activity is low; a consolidation pass would use the quiet "
                "period"]
        return D.NO_ACTION, ["behaviour is within normal complexity bounds"]

    def snapshot(self) -> Dict[str, Any]:
        return {"readings": len(self.history),
                "last": self.history[-1] if self.history else None}
