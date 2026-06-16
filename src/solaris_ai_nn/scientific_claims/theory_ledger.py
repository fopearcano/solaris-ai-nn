"""Theory ledger -- working hypotheses across cycles; theory is not proof.

:class:`TheoryLedger` records the project's theoretical statements (sensorium-
shaped cognition, plural sensorium, perceptual metabolism, proto-concepts,
semiogenesis, sign-based cognition, operational self-boundary, valence/desire as
operational pressure, action-reaction consequence learning, long-horizon
development, replication/falsification, architecture evolution, safety
boundaries). Theory revisions preserve prior versions, contradictions link to
counterevidence, and retired/falsified statements remain archived. Theory is a
hypothesis under evidence, never proof.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


THEORY_AREAS = (
    "sensorium-shaped cognition",
    "plural sensorium",
    "perceptual metabolism",
    "sensorium-native proto-concepts",
    "semiogenesis",
    "sign-based cognition",
    "operational self-boundary",
    "valence/desire as operational pressure",
    "action-reaction consequence learning",
    "long-horizon development",
    "replication/falsification",
    "architecture evolution",
    "safety boundaries",
)


class TheoryStatus:
    WORKING_HYPOTHESIS = "working_hypothesis"
    SUPPORTED_BY_CURRENT_EVIDENCE = "supported_by_current_evidence"
    WEAKLY_SUPPORTED = "weakly_supported"
    INCONCLUSIVE = "inconclusive"
    CHALLENGED = "challenged"
    FALSIFIED = "falsified"
    RETIRED = "retired"
    FORBIDDEN_TO_OVERCLAIM = "forbidden_to_overclaim"

    ALL = (WORKING_HYPOTHESIS, SUPPORTED_BY_CURRENT_EVIDENCE, WEAKLY_SUPPORTED,
           INCONCLUSIVE, CHALLENGED, FALSIFIED, RETIRED, FORBIDDEN_TO_OVERCLAIM)

    # Statuses that must remain archived/visible even when superseded.
    ARCHIVED = (CHALLENGED, FALSIFIED, RETIRED)


@dataclass
class TheoryRevision:
    """One prior version of a theory statement (never overwritten)."""

    text: str
    status: str
    counterevidence_refs: List[str] = field(default_factory=list)
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "status": self.status,
                "counterevidence_refs": list(self.counterevidence_refs),
                "ts": self.ts}


@dataclass
class TheoryStatement:
    """A theoretical statement about one area, with its revision history."""

    theory_id: str
    area: str
    text: str
    status: str = TheoryStatus.WORKING_HYPOTHESIS
    evidence_refs: List[str] = field(default_factory=list)
    counterevidence_refs: List[str] = field(default_factory=list)
    revisions: List[TheoryRevision] = field(default_factory=list)
    ts: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.status not in TheoryStatus.ALL:
            self.status = TheoryStatus.WORKING_HYPOTHESIS

    def revise(self, *, text: str, status: str,
               counterevidence_refs: Optional[List[str]] = None) -> None:
        """Record a revision -- the prior version is archived, never erased."""
        self.revisions.append(TheoryRevision(
            text=self.text, status=self.status,
            counterevidence_refs=list(self.counterevidence_refs)))
        self.text = text
        self.status = status if status in TheoryStatus.ALL \
            else TheoryStatus.INCONCLUSIVE
        if counterevidence_refs:
            for ref in counterevidence_refs:
                if ref not in self.counterevidence_refs:
                    self.counterevidence_refs.append(ref)
        self.ts = time.time()

    @property
    def is_proof(self) -> bool:
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "theory_id": self.theory_id, "area": self.area, "text": self.text,
            "status": self.status, "evidence_refs": list(self.evidence_refs),
            "counterevidence_refs": list(self.counterevidence_refs),
            "revision_count": len(self.revisions),
            "revisions": [r.to_dict() for r in self.revisions],
            "ts": self.ts, "is_proof": False,
            "archived": self.status in TheoryStatus.ARCHIVED,
        }


@dataclass
class TheoryLedger:
    """Holds theory statements; revisions and retired statements stay archived."""

    statements: List[TheoryStatement] = field(default_factory=list)

    def add(self, statement: TheoryStatement) -> TheoryStatement:
        self.statements.append(statement)
        return statement

    def get(self, theory_id: str) -> Optional[TheoryStatement]:
        for s in self.statements:
            if s.theory_id == theory_id:
                return s
        return None

    def revise(self, theory_id: str, *, text: str, status: str,
               counterevidence_refs: Optional[List[str]] = None) -> bool:
        stmt = self.get(theory_id)
        if stmt is None:
            return False
        stmt.revise(text=text, status=status,
                    counterevidence_refs=counterevidence_refs)
        return True

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for s in self.statements:
            out[s.status] = out.get(s.status, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        counts = self.counts()
        return {
            "theory_statement_count": len(self.statements),
            "challenged_count": counts.get(TheoryStatus.CHALLENGED, 0),
            "falsified_count": counts.get(TheoryStatus.FALSIFIED, 0),
            "retired_count": counts.get(TheoryStatus.RETIRED, 0),
            "counts_by_status": counts,
            "statements": [s.to_dict() for s in self.statements],
            "note": "theory is a hypothesis under evidence, not proof; revisions "
                    "preserve prior versions and retired/falsified statements "
                    "remain archived",
        }
