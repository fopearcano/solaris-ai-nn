"""Null models -- could the observed "growth" be noise or accumulation?

A :class:`NullModel` estimates whether an observed signal could be explained by
time passing, raw count accumulation, random ordering, random symbol
stabilization, or a fixed policy. Models are low-compute (stdlib only), never
overstate certainty, and return *inconclusive* when the sample is too small.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class NullModelType:
    RANDOM_METRIC_SHUFFLE = "random_metric_shuffle"
    TIME_INDEX_SHUFFLE = "time_index_shuffle"
    EVENT_ORDER_SHUFFLE = "event_order_shuffle"
    SYMBOL_LABEL_SHUFFLE = "symbol_label_shuffle"
    WORLD_EDGE_SHUFFLE = "world_edge_shuffle"
    ACTION_OUTCOME_SHUFFLE = "action_outcome_shuffle"
    STATIC_NO_LEARNING_MODEL = "static_no_learning_model"

    ALL = (RANDOM_METRIC_SHUFFLE, TIME_INDEX_SHUFFLE, EVENT_ORDER_SHUFFLE,
           SYMBOL_LABEL_SHUFFLE, WORLD_EDGE_SHUFFLE, ACTION_OUTCOME_SHUFFLE,
           STATIC_NO_LEARNING_MODEL)


_MIN_SAMPLE = 8  # below this the result is inconclusive


@dataclass
class NullModelResult:
    """The outcome of one null-model comparison (cautious by design)."""

    null_model_type: str
    observed_value: float
    null_mean: float
    null_std: float
    inconclusive: bool = False
    distinguishable_from_null: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class NullModel:
    """A low-compute null model; stdlib only; never overstates certainty."""

    null_model_type: str
    seed: int = 7
    shuffles: int = 64

    def __post_init__(self) -> None:
        if self.null_model_type not in NullModelType.ALL:
            raise ValueError(f"unknown null model {self.null_model_type!r}")
        self._rng = random.Random(self.seed)

    def evaluate(self, series: List[float],
                 observed_value: Optional[float] = None) -> NullModelResult:
        values = [float(v) for v in (series or [])]
        if self.null_model_type == NullModelType.STATIC_NO_LEARNING_MODEL:
            # A static model never changes; its "growth" is exactly zero.
            obs = observed_value if observed_value is not None else (
                (values[-1] - values[0]) if len(values) >= 2 else 0.0)
            return NullModelResult(
                null_model_type=self.null_model_type, observed_value=obs,
                null_mean=0.0, null_std=0.0,
                inconclusive=len(values) < 2,
                distinguishable_from_null=abs(obs) > 1e-9 and len(values) >= 2,
                notes=["a static no-learning model produces zero change"])
        if len(values) < _MIN_SAMPLE:
            return NullModelResult(
                null_model_type=self.null_model_type,
                observed_value=observed_value or 0.0, null_mean=0.0,
                null_std=0.0, inconclusive=True,
                notes=[f"sample too small (<{_MIN_SAMPLE}); inconclusive"])
        # The observed statistic: the end-to-end trend of the series.
        obs = (observed_value if observed_value is not None
               else values[-1] - values[0])
        # The null distribution: trends of shuffled copies.
        null_trends: List[float] = []
        for _ in range(self.shuffles):
            shuffled = values[:]
            self._rng.shuffle(shuffled)
            null_trends.append(shuffled[-1] - shuffled[0])
        null_mean = statistics.fmean(null_trends)
        null_std = statistics.pstdev(null_trends) or 0.0
        # Distinguishable only if observed is well outside the null spread.
        distinguishable = null_std > 0 and abs(obs - null_mean) > 2 * null_std
        return NullModelResult(
            null_model_type=self.null_model_type, observed_value=round(obs, 4),
            null_mean=round(null_mean, 4), null_std=round(null_std, 4),
            inconclusive=False, distinguishable_from_null=distinguishable,
            notes=["distinguishable only if >2 std from the shuffled null; "
                   "this is a weak, cautious estimate, not a significance test"])

    def snapshot(self) -> Dict[str, Any]:
        return {"null_model_type": self.null_model_type,
                "min_sample": _MIN_SAMPLE, "shuffles": self.shuffles}
