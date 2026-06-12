"""Symbol combinatorics -- which signs recur together, and is that worth
anything?

Observed symbol streams are folded into n-gram sequences (length 2-4).
A sequence is not a sentence: it is a proto-syntactic structure whose
utility must be earned through compression value (one unit instead of
many), transition determinism (does the prefix predict the tail?), and
outcome support (do contexts carrying it end well?).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class SymbolSequence:
    """One recurring ordered tuple of tokens."""

    tokens: Tuple[str, ...]
    count: int = 0
    contexts: List[str] = field(default_factory=list)
    outcome_valences: List[float] = field(default_factory=list)
    utility: float = 0.0
    first_seen: float = field(default_factory=time.time)

    @property
    def key(self) -> str:
        return ">".join(self.tokens)

    def to_dict(self) -> Dict[str, Any]:
        return {"tokens": list(self.tokens), "count": self.count,
                "contexts": self.contexts[-5:],
                "mean_valence": (round(sum(self.outcome_valences)
                                       / len(self.outcome_valences), 4)
                                 if self.outcome_valences else None),
                "utility": self.utility,
                "note": "a proto-syntactic structure, not a sentence"}


@dataclass
class SymbolCombination:
    """An unordered co-occurrence (weaker evidence than a sequence)."""

    tokens: Tuple[str, ...]
    count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"tokens": sorted(self.tokens), "count": self.count}


@dataclass
class SymbolCombinator:
    """Counts n-grams over observed symbol streams."""

    max_ngram: int = 4
    sequences: Dict[str, SymbolSequence] = field(default_factory=dict)
    combinations: Dict[str, SymbolCombination] = field(
        default_factory=dict)
    transition_counts: Dict[str, Dict[str, int]] = field(
        default_factory=dict)
    observations: int = field(default=0, init=False)

    def observe_sequence(self, symbols: List[str],
                         context: Optional[Dict[str, Any]] = None,
                         ) -> List[SymbolSequence]:
        """Fold one symbol stream into n-grams and transitions."""
        ctx = dict(context or {})
        tokens = [str(t) for t in symbols if t]
        touched: List[SymbolSequence] = []
        self.observations += 1
        for n in range(2, min(self.max_ngram, len(tokens)) + 1):
            for i in range(len(tokens) - n + 1):
                gram = tuple(tokens[i:i + n])
                key = ">".join(gram)
                sequence = self.sequences.get(key)
                if sequence is None:
                    sequence = SymbolSequence(tokens=gram)
                    self.sequences[key] = sequence
                sequence.count += 1
                label = str(ctx.get("label", ""))
                if label and label not in sequence.contexts:
                    sequence.contexts.append(label)
                valence = ctx.get("outcome_valence")
                if valence is not None:
                    sequence.outcome_valences.append(float(valence))
                    sequence.outcome_valences = \
                        sequence.outcome_valences[-20:]
                touched.append(sequence)
        for i in range(len(tokens) - 1):
            prefix = tokens[i]
            self.transition_counts.setdefault(prefix, {})
            self.transition_counts[prefix][tokens[i + 1]] = \
                self.transition_counts[prefix].get(tokens[i + 1], 0) + 1
        if len(tokens) >= 2:
            combo_key = "+".join(sorted(set(tokens)))
            combo = self.combinations.get(combo_key)
            if combo is None:
                combo = SymbolCombination(tokens=tuple(sorted(
                    set(tokens))))
                self.combinations[combo_key] = combo
            combo.count += 1
        return touched

    # -- queries ------------------------------------------------------------------

    def find_repeated_sequences(self, min_count: int = 3,
                                ) -> List[SymbolSequence]:
        return sorted([s for s in self.sequences.values()
                       if s.count >= min_count],
                      key=lambda s: (-s.count, s.key))

    def score_sequence_utility(self, sequence: SymbolSequence) -> float:
        """Compression + determinism + outcome support, in [0, 1]."""
        compression = min(1.0, (len(sequence.tokens) - 1)
                          * sequence.count / 20.0)
        determinism = 0.0
        prefix = sequence.tokens[-2]
        transitions = self.transition_counts.get(prefix, {})
        total = sum(transitions.values())
        if total:
            determinism = transitions.get(sequence.tokens[-1],
                                          0) / total
        outcome = 0.0
        if sequence.outcome_valences:
            outcome = max(0.0, sum(sequence.outcome_valences)
                          / len(sequence.outcome_valences))
        sequence.utility = round(min(1.0, 0.4 * compression
                                     + 0.4 * determinism
                                     + 0.2 * outcome), 4)
        return sequence.utility

    def snapshot(self) -> Dict[str, Any]:
        repeated = self.find_repeated_sequences()
        return {
            "observations": self.observations,
            "sequence_count": len(self.sequences),
            "repeated_sequence_count": len(repeated),
            "combination_count": len(self.combinations),
            "top_sequences": [s.to_dict() for s in repeated[:5]],
            "note": "sequences are proto-syntactic structures, not "
                    "sentences; utility is measured, never assumed",
        }
