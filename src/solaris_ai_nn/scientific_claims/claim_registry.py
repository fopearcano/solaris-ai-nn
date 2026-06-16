"""Scientific claim registry -- every claim, its status, and its evidence.

:class:`ClaimRegistry` is the append-only registry of scientific claims. Every
claim carries evidence refs or an explicit missing-evidence reason; unsupported,
contradicted, and falsified claims stay visible; forbidden claims are blocked, not
deleted. The registry records what *may* be claimed from the evidence -- it proves
nothing about consciousness, life, or agency.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ClaimCategory:
    ARCHITECTURE = "architecture_claim"
    SENSORIUM = "sensorium_claim"
    DEVELOPMENTAL = "developmental_claim"
    REPLICATION = "replication_claim"
    FALSIFICATION = "falsification_claim"
    SAFETY = "safety_claim"
    IMPLEMENTATION = "implementation_claim"
    BASELINE = "baseline_claim"
    NEGATIVE_RESULT = "negative_result_claim"
    INCONCLUSIVE = "inconclusive_claim"
    SPECULATIVE_THEORY = "speculative_theory_claim"
    FORBIDDEN = "forbidden_claim"

    ALL = (ARCHITECTURE, SENSORIUM, DEVELOPMENTAL, REPLICATION, FALSIFICATION,
           SAFETY, IMPLEMENTATION, BASELINE, NEGATIVE_RESULT, INCONCLUSIVE,
           SPECULATIVE_THEORY, FORBIDDEN)


class ClaimStatus:
    SUPPORTED = "supported"
    WEAKLY_SUPPORTED = "weakly_supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    INCONCLUSIVE = "inconclusive"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"
    FALSIFIED = "falsified"
    FORBIDDEN = "forbidden"
    REQUIRES_MORE_EVIDENCE = "requires_more_evidence"
    UNKNOWN = "unknown"

    ALL = (SUPPORTED, WEAKLY_SUPPORTED, PARTIALLY_SUPPORTED, INCONCLUSIVE,
           UNSUPPORTED, CONTRADICTED, FALSIFIED, FORBIDDEN,
           REQUIRES_MORE_EVIDENCE, UNKNOWN)

    # Statuses that must always stay visible (never silently dropped).
    PRESERVED = (UNSUPPORTED, CONTRADICTED, FALSIFIED, FORBIDDEN)
    # Statuses that may appear in a publication as positive claims.
    PUBLISHABLE = (SUPPORTED, WEAKLY_SUPPORTED, PARTIALLY_SUPPORTED)


@dataclass
class ScientificClaim:
    """One scientific claim with its category, status, and evidence refs."""

    claim_id: str
    text: str
    category: str = ClaimCategory.ARCHITECTURE
    status: str = ClaimStatus.UNKNOWN
    evidence_refs: List[str] = field(default_factory=list)
    counterevidence_refs: List[str] = field(default_factory=list)
    missing_evidence_reason: str = ""
    strength: str = "none"
    limitation_refs: List[str] = field(default_factory=list)
    publishable_in: List[str] = field(default_factory=list)
    detail: str = ""
    ts: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.category not in ClaimCategory.ALL:
            self.category = ClaimCategory.SPECULATIVE_THEORY
        if self.status not in ClaimStatus.ALL:
            self.status = ClaimStatus.UNKNOWN

    @property
    def has_evidence_basis(self) -> bool:
        """A claim must have evidence refs or an explicit missing reason."""
        return bool(self.evidence_refs) or bool(self.missing_evidence_reason)

    @property
    def is_supported(self) -> bool:
        return self.status in ClaimStatus.PUBLISHABLE

    @property
    def is_blocked(self) -> bool:
        return self.status in (ClaimStatus.FORBIDDEN, ClaimStatus.FALSIFIED,
                               ClaimStatus.CONTRADICTED)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id, "text": self.text,
            "category": self.category, "status": self.status,
            "evidence_refs": list(self.evidence_refs),
            "counterevidence_refs": list(self.counterevidence_refs),
            "missing_evidence_reason": self.missing_evidence_reason,
            "strength": self.strength,
            "limitation_refs": list(self.limitation_refs),
            "publishable_in": list(self.publishable_in),
            "detail": self.detail, "ts": self.ts,
            "has_evidence_basis": self.has_evidence_basis,
            "is_supported": self.is_supported,
            "is_blocked": self.is_blocked,
            "is_consciousness_or_personhood": False,
        }


@dataclass
class ClaimRegistry:
    """Append-only registry; unsupported/falsified/forbidden claims stay visible."""

    state_dir: str = ".solaris_ai_nn_claims"
    persist: bool = True
    claims: List[ScientificClaim] = field(default_factory=list, init=False)

    @property
    def _registry_path(self) -> str:
        return os.path.join(self.state_dir, "claim_registry.json")

    @property
    def _history_path(self) -> str:
        return os.path.join(self.state_dir, "claim_history.jsonl")

    def add(self, claim: ScientificClaim) -> ScientificClaim:
        # Every claim must have an evidence basis; otherwise it is unsupported
        # with an explicit reason (it is never silently dropped).
        if not claim.has_evidence_basis:
            claim.missing_evidence_reason = (
                claim.missing_evidence_reason or "no evidence ref supplied")
            if claim.status in ClaimStatus.PUBLISHABLE:
                claim.status = ClaimStatus.UNSUPPORTED
        self.claims.append(claim)
        if self.persist:
            self._append_history(claim)
            self._write_registry()
        return claim

    def get(self, claim_id: str) -> Optional[ScientificClaim]:
        for c in self.claims:
            if c.claim_id == claim_id:
                return c
        return None

    def by_status(self, status: str) -> List[ScientificClaim]:
        return [c for c in self.claims if c.status == status]

    def by_category(self, category: str) -> List[ScientificClaim]:
        return [c for c in self.claims if c.category == category]

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for c in self.claims:
            out[c.status] = out.get(c.status, 0) + 1
        return out

    def _append_history(self, claim: ScientificClaim) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._history_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(claim.to_dict(), default=str) + "\n")

    def _write_registry(self) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._registry_path, "w", encoding="utf-8") as fh:
            json.dump(self.index(), fh, indent=2, default=str)

    def index(self) -> Dict[str, Any]:
        counts = self.counts()
        return {
            "scientific_claim_count": len(self.claims),
            "supported_claim_count": counts.get(ClaimStatus.SUPPORTED, 0),
            "weakly_supported_claim_count": counts.get(
                ClaimStatus.WEAKLY_SUPPORTED, 0),
            "partially_supported_claim_count": counts.get(
                ClaimStatus.PARTIALLY_SUPPORTED, 0),
            "inconclusive_claim_count": counts.get(ClaimStatus.INCONCLUSIVE, 0),
            "unsupported_claim_count": counts.get(ClaimStatus.UNSUPPORTED, 0),
            "contradicted_claim_count": counts.get(ClaimStatus.CONTRADICTED, 0),
            "falsified_claim_count": counts.get(ClaimStatus.FALSIFIED, 0),
            "forbidden_claim_count": counts.get(ClaimStatus.FORBIDDEN, 0),
            "requires_more_evidence_count": counts.get(
                ClaimStatus.REQUIRES_MORE_EVIDENCE, 0),
            "counts_by_status": counts,
            "append_only": True,
        }

    def to_dict(self) -> Dict[str, Any]:
        d = self.index()
        d["claims"] = [c.to_dict() for c in self.claims]
        d["note"] = ("append-only claim registry; unsupported, contradicted, "
                     "and falsified claims stay visible and forbidden claims are "
                     "blocked, not deleted; it proves nothing about "
                     "consciousness, life, or agency")
        return d
