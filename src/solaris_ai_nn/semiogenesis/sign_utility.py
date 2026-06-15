"""Sign utility -- evidence-backed structural usefulness of a sign.

The :class:`SignUtilityEvaluator` scores a sign's compression, prediction,
attention, memory-retrieval, hypothesis, LOGOS, and world-model-relation utility.
A useful sign is not therefore true and not therefore understood; signs with no
utility may decay.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .signs import InternalSign, SignStatus


@dataclass
class SignUtilityResult:
    sign_id: str
    compression_utility: float
    prediction_utility: float
    attention_utility: float
    memory_retrieval_utility: float
    hypothesis_utility: float
    logos_utility: float
    world_model_relation_utility: float
    overall: float
    useful: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_id": self.sign_id,
            "compression_utility": round(self.compression_utility, 4),
            "prediction_utility": round(self.prediction_utility, 4),
            "attention_utility": round(self.attention_utility, 4),
            "memory_retrieval_utility": round(self.memory_retrieval_utility, 4),
            "hypothesis_utility": round(self.hypothesis_utility, 4),
            "logos_utility": round(self.logos_utility, 4),
            "world_model_relation_utility": round(
                self.world_model_relation_utility, 4),
            "overall": round(self.overall, 4),
            "useful": self.useful,
            "note": "structural utility only; a useful sign is not therefore "
                    "true or understood",
        }


@dataclass
class SignUtilityEvaluator:
    """Scores sign utility from evidence and flags low-utility signs."""

    useful_threshold: float = 0.25

    def evaluate(self, sign: InternalSign) -> SignUtilityResult:
        memory = min(1.0, 0.1 * sign.recurrence_count)
        hypothesis = sign.metadata.get("hypothesis_utility", 0.0)
        logos = sign.metadata.get("logos_utility",
                                  0.5 if sign.kind == "LOGOS_tension_sign"
                                  else 0.0)
        overall = round((sign.compression_utility + sign.prediction_utility
                         + sign.attention_utility + memory
                         + float(hypothesis) + float(logos)
                         + sign.relation_utility) / 7.0, 4)
        useful = overall >= self.useful_threshold
        # A useless sign (and not contaminated, which we keep marked) is nudged
        # toward instability; signs never get deleted here.
        if not useful and sign.status == SignStatus.STABLE:
            sign.status = SignStatus.AMBIGUOUS
            if "low utility; provisionally demoted from stable" \
                    not in sign.limitations:
                sign.limitations.append(
                    "low utility; provisionally demoted from stable")
        return SignUtilityResult(
            sign_id=sign.sign_id,
            compression_utility=sign.compression_utility,
            prediction_utility=sign.prediction_utility,
            attention_utility=sign.attention_utility,
            memory_retrieval_utility=memory,
            hypothesis_utility=float(hypothesis), logos_utility=float(logos),
            world_model_relation_utility=sign.relation_utility,
            overall=overall, useful=useful)

    def evaluate_all(self, signs: List[InternalSign]) -> List[SignUtilityResult]:
        return [self.evaluate(s) for s in signs]

    @staticmethod
    def means(signs: List[InternalSign]) -> Dict[str, float]:
        if not signs:
            return {"compression": 0.0, "prediction": 0.0, "attention": 0.0}
        n = len(signs)
        return {
            "compression": round(
                sum(s.compression_utility for s in signs) / n, 4),
            "prediction": round(
                sum(s.prediction_utility for s in signs) / n, 4),
            "attention": round(
                sum(s.attention_utility for s in signs) / n, 4),
        }
