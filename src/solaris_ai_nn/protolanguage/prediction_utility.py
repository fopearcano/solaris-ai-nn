"""Prediction utility -- the semantic test: do symbols help foresight?

Counts, recency, and simple Markov-style transitions -- no heavy ML.
Symbol-conditioned prediction is compared against a frequency baseline,
and a *negative* improvement is reported exactly as honestly as a
positive one: a symbol system that does not predict is a finding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SymbolPredictionEvaluator:
    """Markov-style next-token prediction with a frequency baseline."""

    transitions: Dict[Tuple[str, ...], Dict[str, int]] = field(
        default_factory=dict)
    global_counts: Dict[str, int] = field(default_factory=dict)
    order: int = 2
    trained_sequences: int = field(default=0, init=False)
    scored: int = field(default=0, init=False)
    hits: int = field(default=0, init=False)
    baseline_hits: int = field(default=0, init=False)

    # -- training -----------------------------------------------------------------

    def train_counts(self, symbol_sequences: List[List[str]]) -> None:
        for sequence in symbol_sequences:
            tokens = [str(t) for t in sequence if t]
            self.trained_sequences += 1
            for token in tokens:
                self.global_counts[token] = \
                    self.global_counts.get(token, 0) + 1
            for n in (1, min(self.order, 2)):
                for i in range(len(tokens) - n):
                    context = tuple(tokens[i:i + n])
                    nxt = tokens[i + n]
                    bucket = self.transitions.setdefault(context, {})
                    bucket[nxt] = bucket.get(nxt, 0) + 1

    # -- prediction ----------------------------------------------------------------

    def predict_next(self, sequence_context: List[str],
                     ) -> "tuple[Optional[str], float]":
        """(predicted token, probability); longest context wins."""
        tokens = [str(t) for t in sequence_context if t]
        for n in range(min(self.order, len(tokens)), 0, -1):
            context = tuple(tokens[-n:])
            bucket = self.transitions.get(context)
            if bucket:
                best = max(sorted(bucket), key=lambda t: bucket[t])
                total = sum(bucket.values())
                return (best, round(bucket[best] / total, 4))
        return (self.predict_baseline()[0], 0.0)

    def predict_baseline(self) -> "tuple[Optional[str], float]":
        """Frequency baseline: the globally most common token."""
        if not self.global_counts:
            return (None, 0.0)
        best = max(sorted(self.global_counts),
                   key=lambda t: self.global_counts[t])
        total = sum(self.global_counts.values())
        return (best, round(self.global_counts[best] / total, 4))

    def score_prediction(self, prediction: Optional[str],
                         actual: str) -> bool:
        self.scored += 1
        hit = prediction == actual
        if hit:
            self.hits += 1
        baseline, _ = self.predict_baseline()
        if baseline == actual:
            self.baseline_hits += 1
        return hit

    # -- evaluation ----------------------------------------------------------------

    def evaluate_holdout(self, holdout_sequences: List[List[str]],
                         ) -> Dict[str, Any]:
        """Score symbolic vs baseline over held-out sequences."""
        for sequence in holdout_sequences:
            tokens = [str(t) for t in sequence if t]
            for i in range(1, len(tokens)):
                prediction, _ = self.predict_next(tokens[:i])
                self.score_prediction(prediction, tokens[i])
        return self.compare_with_baseline()

    def compare_with_baseline(self) -> Dict[str, Any]:
        symbolic = (round(self.hits / self.scored, 4)
                    if self.scored else None)
        baseline = (round(self.baseline_hits / self.scored, 4)
                    if self.scored else None)
        improvement = (round(symbolic - baseline, 4)
                       if symbolic is not None and baseline is not None
                       else None)
        return {
            "predictions_scored": self.scored,
            "symbolic_accuracy": symbolic,
            "baseline_accuracy": baseline,
            "improvement_over_baseline": improvement,
            "improved": (improvement is not None and improvement > 0),
            "note": "counts and Markov-style transitions only; a "
                    "negative improvement is reported as honestly as a "
                    "positive one",
        }

    def update_symbol_scores(self, registry: Any) -> None:
        """Feed measured prediction value back into the symbols."""
        comparison = self.compare_with_baseline()
        improvement = comparison.get("improvement_over_baseline")
        if improvement is None:
            return
        gain = max(0.0, min(1.0, improvement * 2))
        for context, bucket in self.transitions.items():
            for token in list(context) + list(bucket):
                symbol = registry.find_by_token(token)
                if symbol is not None:
                    symbol.prediction_score = round(
                        max(symbol.prediction_score, gain), 4)
                    symbol.recompute_confidence()

    def snapshot(self) -> Dict[str, Any]:
        return {"trained_sequences": self.trained_sequences,
                "transition_contexts": len(self.transitions),
                **self.compare_with_baseline()}
