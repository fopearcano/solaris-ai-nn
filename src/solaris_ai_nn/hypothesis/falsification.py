"""Falsification -- careful, bounded verdicts on hypotheses.

The :class:`FalsificationEngine` compares expected vs observed outcomes and
returns a verdict (supported / weakened / falsified / inconclusive), then
nudges confidence by a *bounded* amount. It deliberately does not overstate
support: one success rarely proves anything, and offline-only support cannot
fully promote a hypothesis. One clear failure can weaken or falsify depending
on the design.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .evidence import EvidenceRecord, EvidenceType
from .hypotheses import Hypothesis, HypothesisConfidence, HypothesisStatus


@dataclass
class FalsificationResult:
    """The verdict on one hypothesis given one piece of evidence."""

    hypothesis_id: str
    verdict: str  # supported | weakened | falsified | inconclusive
    confidence_delta: float = 0.0
    reason: str = ""
    offline_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


# Evidence type -> (verdict, base confidence delta).
_VERDICT = {
    EvidenceType.SUPPORTING: (HypothesisStatus.SUPPORTED, 0.12),
    EvidenceType.WEAKENING: (HypothesisStatus.WEAKENED, -0.1),
    EvidenceType.FALSIFYING: (HypothesisStatus.FALSIFIED, -0.2),
    EvidenceType.INCONCLUSIVE: (HypothesisStatus.INCONCLUSIVE, 0.0),
    EvidenceType.UNSAFE: (HypothesisStatus.UNSAFE_TO_TEST, 0.0),
    EvidenceType.OFFLINE_SIMULATED: (HypothesisStatus.INCONCLUSIVE, 0.05),
    EvidenceType.NURSERY_SIMULATED: (HypothesisStatus.SUPPORTED, 0.1),
    EvidenceType.LATENT_REPLAY: (HypothesisStatus.INCONCLUSIVE, 0.05),
    EvidenceType.OBSERVED_REAL_STREAM: (HypothesisStatus.SUPPORTED, 0.12),
}


@dataclass
class FalsificationEngine:
    """Turns evidence into careful, bounded status/confidence changes."""

    # Offline support alone cannot promote past this confidence ceiling.
    offline_confidence_ceiling: float = 0.6
    verdicts: List[Dict[str, Any]] = field(default_factory=list)

    def evaluate(self, hypothesis: Hypothesis,
                 evidence: EvidenceRecord) -> FalsificationResult:
        status, base_delta = _VERDICT.get(
            evidence.evidence_type,
            (HypothesisStatus.INCONCLUSIVE, 0.0))
        offline_only = evidence.is_offline
        reason = (f"{evidence.evidence_type} evidence from "
                  f"{evidence.source_scope}: {evidence.observation}")
        # Offline evidence is downgraded toward inconclusive for support.
        if offline_only and status == HypothesisStatus.SUPPORTED:
            status = HypothesisStatus.INCONCLUSIVE
            base_delta = min(base_delta, 0.05)
            reason += " (offline-only: cannot fully promote)"
        verdict_map = {
            HypothesisStatus.SUPPORTED: "supported",
            HypothesisStatus.WEAKENED: "weakened",
            HypothesisStatus.FALSIFIED: "falsified",
            HypothesisStatus.INCONCLUSIVE: "inconclusive",
            HypothesisStatus.UNSAFE_TO_TEST: "inconclusive",
        }
        result = FalsificationResult(
            hypothesis_id=hypothesis.hypothesis_id,
            verdict=verdict_map.get(status, "inconclusive"),
            confidence_delta=base_delta, reason=reason,
            offline_only=offline_only)
        self.verdicts.append(result.to_dict())
        self.verdicts = self.verdicts[-200:]
        return result

    def update_confidence(self, hypothesis: Hypothesis,
                          result: FalsificationResult) -> None:
        """Apply a bounded confidence change and set the status carefully."""
        new_conf = HypothesisConfidence.bounded_update(
            hypothesis.confidence, result.confidence_delta)
        if result.offline_only:
            new_conf = min(new_conf, self.offline_confidence_ceiling)
        hypothesis.confidence = new_conf
        hypothesis.uncertainty = round(1.0 - new_conf, 4)
        # Status transitions are careful: supported requires real/simulated
        # evidence; one offline pass stays inconclusive.
        if result.verdict == "falsified":
            hypothesis.set_status(HypothesisStatus.FALSIFIED)
        elif result.verdict == "weakened":
            hypothesis.set_status(HypothesisStatus.WEAKENED)
        elif result.verdict == "supported":
            hypothesis.set_status(HypothesisStatus.SUPPORTED)
        else:
            hypothesis.set_status(HypothesisStatus.INCONCLUSIVE)

    def snapshot(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for v in self.verdicts:
            counts[v["verdict"]] = counts.get(v["verdict"], 0) + 1
        return {"verdicts_total": len(self.verdicts), "by_verdict": counts,
                "recent": self.verdicts[-5:]}
