"""AnticipationTracker -- simple one-step predictions, honestly scored.

No deep learning: predictions come from transition frequencies, recency, and
the readout's own tendencies. Every prediction is scored against what
actually happened next, and the tracker keeps the receipts (hits, misses,
streaks, rolling accuracy, a surprise estimate).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def valence_bucket(valence: Optional[float]) -> str:
    if valence is None:
        return "none"
    if valence > 0.15:
        return "positive"
    if valence < -0.15:
        return "negative"
    return "neutral"


@dataclass
class AnticipationPrediction:
    """One one-step-ahead prediction with its basis."""

    next_signal_kind: Optional[str] = None
    next_action: Optional[str] = None
    next_valence_bucket: str = "none"
    absence_probability: float = 0.0
    activity_trend: str = "stable"
    basis: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AnticipationTracker:
    """Frequency/recency-based one-step anticipation."""

    rolling_window: int = 50

    # transition counts: last signal kind -> Counter(next kind)
    _kind_transitions: Dict[str, Counter] = field(
        default_factory=lambda: defaultdict(Counter), init=False)
    _last_kind: Optional[str] = field(default=None, init=False)
    _action_counts: Counter = field(default_factory=Counter, init=False)
    _valence_buckets: Counter = field(default_factory=Counter, init=False)
    _absence_history: List[bool] = field(default_factory=list, init=False)
    _norm_history: List[float] = field(default_factory=list, init=False)
    _pending: Optional[AnticipationPrediction] = field(default=None,
                                                       init=False)
    _outcomes: List[bool] = field(default_factory=list, init=False)

    prediction_count: int = field(default=0, init=False)
    hit_count: int = field(default=0, init=False)
    miss_count: int = field(default=0, init=False)
    miss_streak: int = field(default=0, init=False)
    last_score: Optional[Dict[str, Any]] = field(default=None, init=False)

    # -- prediction ---------------------------------------------------------------

    def predict(self, context: Optional[Dict[str, Any]] = None,
                ) -> AnticipationPrediction:
        """Predict the next step from what has been seen so far."""
        ctx = context or {}
        # Next signal kind: most frequent successor of the last kind.
        next_kind = None
        if self._last_kind and self._kind_transitions[self._last_kind]:
            next_kind = self._kind_transitions[
                self._last_kind].most_common(1)[0][0]
        elif self._kind_transitions:
            merged: Counter = Counter()
            for counter in self._kind_transitions.values():
                merged.update(counter)
            if merged:
                next_kind = merged.most_common(1)[0][0]

        # Next action: the readout's standing tendency, else the modal action.
        next_action = ctx.get("suggested_action")
        if next_action is None and self._action_counts:
            next_action = self._action_counts.most_common(1)[0][0]

        bucket = (self._valence_buckets.most_common(1)[0][0]
                  if self._valence_buckets else "none")
        recent_absence = self._absence_history[-self.rolling_window:]
        absence_p = (sum(recent_absence) / len(recent_absence)
                     if recent_absence else 0.0)

        trend = "stable"
        if len(self._norm_history) >= 4:
            recent = self._norm_history[-4:]
            delta = recent[-1] - recent[0]
            if delta > 0.05 * max(1e-9, abs(recent[0])):
                trend = "rising"
            elif delta < -0.05 * max(1e-9, abs(recent[0])):
                trend = "falling"

        prediction = AnticipationPrediction(
            next_signal_kind=next_kind, next_action=next_action,
            next_valence_bucket=bucket,
            absence_probability=round(absence_p, 4), activity_trend=trend,
            basis={"last_kind": self._last_kind,
                   "observations": sum(
                       sum(c.values())
                       for c in self._kind_transitions.values())})
        self._pending = prediction
        return prediction

    # -- observation ----------------------------------------------------------------

    def observe_actual(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Record what actually happened; scores the pending prediction."""
        kind = event.get("input_type") or event.get("kind")
        action = event.get("suggested_action") or event.get("action")
        valence = event.get("valence")
        is_absence = bool(event.get("is_absence", False))
        state_norm = event.get("reservoir_energy", event.get("state_norm"))

        score = None
        if self._pending is not None:
            score = self.score_prediction(self._pending, {
                "kind": kind, "action": action, "valence": valence,
                "is_absence": is_absence, "state_norm": state_norm})
            self._pending = None

        # Update the statistics with the actual outcome.
        if kind is not None:
            if self._last_kind is not None:
                self._kind_transitions[self._last_kind][kind] += 1
            self._last_kind = kind
        if action is not None:
            self._action_counts[action] += 1
        if valence is not None:
            self._valence_buckets[valence_bucket(float(valence))] += 1
        self._absence_history.append(is_absence)
        self._absence_history = self._absence_history[-500:]
        if state_norm is not None:
            self._norm_history.append(float(state_norm))
            self._norm_history = self._norm_history[-100:]
        return score

    def score_prediction(self, prediction: AnticipationPrediction,
                         actual: Dict[str, Any]) -> Dict[str, Any]:
        """Per-field hits; the prediction counts as a hit if most fields hit."""
        fields: Dict[str, bool] = {}
        if prediction.next_signal_kind is not None \
                and actual.get("kind") is not None:
            fields["signal_kind"] = (prediction.next_signal_kind
                                     == actual["kind"])
        if prediction.next_action is not None \
                and actual.get("action") is not None:
            fields["action"] = prediction.next_action == actual["action"]
        if actual.get("valence") is not None \
                and prediction.next_valence_bucket != "none":
            fields["valence_bucket"] = (
                prediction.next_valence_bucket
                == valence_bucket(float(actual["valence"])))
        fields["absence"] = ((prediction.absence_probability >= 0.5)
                             == bool(actual.get("is_absence", False)))

        hits = sum(fields.values())
        hit = hits >= max(1, (len(fields) + 1) // 2)
        self.prediction_count += 1
        if hit:
            self.hit_count += 1
            self.miss_streak = 0
        else:
            self.miss_count += 1
            self.miss_streak += 1
        self._outcomes.append(hit)
        self._outcomes = self._outcomes[-self.rolling_window:]
        self.last_score = {"hit": hit, "fields": fields,
                           "prediction": prediction.to_dict()}
        return self.last_score

    # -- metrics -----------------------------------------------------------------------

    def rolling_accuracy(self) -> float:
        if not self._outcomes:
            return 0.0
        return sum(self._outcomes) / len(self._outcomes)

    def surprise_estimate(self) -> float:
        """How surprising the recent world has been: 1 - rolling accuracy,
        nudged up by an active miss streak."""
        base = 1.0 - self.rolling_accuracy()
        return round(min(1.0, base + 0.05 * min(self.miss_streak, 5)), 4)

    def anticipation_loss(self) -> float:
        if self.prediction_count == 0:
            return 0.0
        return round(self.miss_count / self.prediction_count, 4)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "prediction_count": self.prediction_count,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "rolling_accuracy": round(self.rolling_accuracy(), 4),
            "miss_streak": self.miss_streak,
            "surprise_estimate": self.surprise_estimate(),
            "anticipation_loss": self.anticipation_loss(),
            "last_score": self.last_score,
        }
