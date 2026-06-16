"""Replication matrix -- a conservative grid of what replicated and what did not.

:class:`ReplicationMatrixBuilder` assembles the cross-run findings (structural
similarity per dimension, divergences, and falsification outcomes) into a grid of
:class:`ReplicationMatrixCell`s. The matrix is deliberately conservative: there
is no empty green dashboard, inconclusive is a valid status, and falsified claims
are made prominent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReplicationCellStatus:
    REPLICATED = "replicated"
    PARTIALLY_REPLICATED = "partially_replicated"
    DIVERGED = "diverged"
    INCONCLUSIVE = "inconclusive"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    FALSIFIED = "falsified"
    NOT_APPLICABLE = "not_applicable"

    ALL = (REPLICATED, PARTIALLY_REPLICATED, DIVERGED, INCONCLUSIVE, FAILED,
           UNAVAILABLE, FALSIFIED, NOT_APPLICABLE)


@dataclass
class ReplicationMatrixCell:
    """One claim x axis cell with a conservative status + evidence."""

    claim: str
    axis: str
    status: str
    detail: str = ""
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"claim": self.claim, "axis": self.axis, "status": self.status,
                "detail": self.detail, "evidence_refs": list(self.evidence_refs)}


@dataclass
class ReplicationMatrix:
    """A conservative grid; falsified claims are prominent; inconclusive valid."""

    cells: List[ReplicationMatrixCell] = field(default_factory=list)

    def add(self, claim: str, axis: str, status: str, *, detail: str = "",
            evidence_refs: Optional[List[str]] = None) -> ReplicationMatrixCell:
        if status not in ReplicationCellStatus.ALL:
            status = ReplicationCellStatus.INCONCLUSIVE
        cell = ReplicationMatrixCell(claim=claim, axis=axis, status=status,
                                     detail=detail,
                                     evidence_refs=list(evidence_refs or []))
        self.cells.append(cell)
        return cell

    def counts(self) -> Dict[str, int]:
        out = {s: 0 for s in ReplicationCellStatus.ALL}
        for c in self.cells:
            out[c.status] = out.get(c.status, 0) + 1
        return out

    def falsified_cells(self) -> List[ReplicationMatrixCell]:
        return [c for c in self.cells
                if c.status == ReplicationCellStatus.FALSIFIED]

    def to_dict(self) -> Dict[str, Any]:
        counts = self.counts()
        return {
            "cell_count": len(self.cells),
            "cells": [c.to_dict() for c in self.cells],
            "counts": counts,
            "replicated_claim_count": counts[ReplicationCellStatus.REPLICATED],
            "partially_replicated_claim_count":
                counts[ReplicationCellStatus.PARTIALLY_REPLICATED],
            "diverged_claim_count": counts[ReplicationCellStatus.DIVERGED],
            "inconclusive_claim_count":
                counts[ReplicationCellStatus.INCONCLUSIVE],
            "falsified_claim_count": counts[ReplicationCellStatus.FALSIFIED],
            "failed_claim_count": counts[ReplicationCellStatus.FAILED],
            "unavailable_claim_count": counts[ReplicationCellStatus.UNAVAILABLE],
            "falsified_claims": [c.to_dict() for c in self.falsified_cells()],
            "empty_green_dashboard": False,
            "note": ("conservative replication grid; inconclusive is valid and "
                     "falsified claims are prominent; replication compares "
                     "observable structures only, not consciousness or life"),
        }


@dataclass
class ReplicationMatrixBuilder:
    """Builds the conservative replication matrix from cross-run findings."""

    def build(self, *, similarity_results: Optional[List[Dict]] = None,
              divergences: Optional[List[Dict]] = None,
              falsification_results: Optional[List[Dict]] = None,
              unavailable_arms: Optional[List[str]] = None,
              ) -> ReplicationMatrix:
        matrix = ReplicationMatrix()
        similarity_results = similarity_results or []
        divergences = divergences or []
        falsification_results = falsification_results or []

        # Structural-similarity cells: per measured dimension across a pair.
        for sim in similarity_results:
            axis = f"{sim.get('run_a')}~{sim.get('run_b')}"
            scores = sim.get("scores", {})
            if not scores:
                matrix.add("structural_similarity", axis,
                           ReplicationCellStatus.INCONCLUSIVE,
                           detail="no measurable dimensions",
                           evidence_refs=["similarity:none"])
                continue
            for dim, score in scores.items():
                status = (ReplicationCellStatus.REPLICATED if score >= 0.6
                          else ReplicationCellStatus.PARTIALLY_REPLICATED
                          if score >= 0.3 else ReplicationCellStatus.DIVERGED)
                matrix.add(dim, axis, status, detail=f"similarity {score:.2f}",
                           evidence_refs=[f"similarity:{dim}"])

        # Divergence cells: a documented divergence is a diverged claim.
        for div in divergences:
            axis = f"{div.get('run_a')}~{div.get('run_b')}"
            status = (ReplicationCellStatus.FAILED if div.get("is_failure")
                      else ReplicationCellStatus.DIVERGED)
            matrix.add(f"divergence:{div.get('reason')}", axis, status,
                       detail=div.get("evidence", ""),
                       evidence_refs=[f"divergence:{div.get('reason')}"])

        # Falsification cells: falsified claims are prominent.
        for fr in falsification_results:
            outcome = fr.get("outcome")
            status = {
                "falsified": ReplicationCellStatus.FALSIFIED,
                "passed": ReplicationCellStatus.REPLICATED,
                "inconclusive": ReplicationCellStatus.INCONCLUSIVE,
            }.get(outcome, ReplicationCellStatus.INCONCLUSIVE)
            matrix.add(f"falsification:{fr.get('test_type')}",
                       "falsification", status,
                       detail=fr.get("claim", ""),
                       evidence_refs=[f"falsification:{fr.get('test_type')}"])

        # Unavailable arms: explicit unavailable cells (no silent green).
        for arm in (unavailable_arms or []):
            matrix.add(f"arm:{arm}", "plan",
                       ReplicationCellStatus.UNAVAILABLE,
                       detail="arm artifacts unavailable",
                       evidence_refs=[f"plan:{arm}"])

        if not matrix.cells:
            matrix.add("replication", "overall",
                       ReplicationCellStatus.INCONCLUSIVE,
                       detail="insufficient runs/artifacts to populate the "
                              "matrix",
                       evidence_refs=["matrix:empty"])
        return matrix
