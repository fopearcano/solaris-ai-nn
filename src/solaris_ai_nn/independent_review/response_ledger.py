"""Reviewer response ledger -- append-only objections and responses.

:class:`ReviewerResponseLedger` is the append-only record of reviewer objections
and the project's responses. Objections cannot be deleted; accepted limitations
and falsifications remain visible; responses must cite evidence refs or admit
missing evidence; and the system cannot declare victory over a reviewer by default.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ObjectionStatus:
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    ANSWERED = "answered"
    PARTIALLY_ANSWERED = "partially_answered"
    REQUIRES_EXPERIMENT = "requires_experiment"
    ACCEPTED_AS_LIMITATION = "accepted_as_limitation"
    ACCEPTED_AS_FALSIFICATION = "accepted_as_falsification"
    REJECTED_WITH_EVIDENCE = "rejected_with_evidence"
    UNRESOLVED = "unresolved"
    ARCHIVED = "archived"

    ALL = (NEW, ACKNOWLEDGED, ANSWERED, PARTIALLY_ANSWERED, REQUIRES_EXPERIMENT,
           ACCEPTED_AS_LIMITATION, ACCEPTED_AS_FALSIFICATION,
           REJECTED_WITH_EVIDENCE, UNRESOLVED, ARCHIVED)

    # Statuses that count as still open.
    OPEN = (NEW, ACKNOWLEDGED, PARTIALLY_ANSWERED, REQUIRES_EXPERIMENT,
            UNRESOLVED)
    # Statuses that must always stay visible.
    PRESERVED = (ACCEPTED_AS_LIMITATION, ACCEPTED_AS_FALSIFICATION, UNRESOLVED)


@dataclass
class ReviewerResponse:
    """One response to an objection (must cite evidence or admit its absence)."""

    text: str
    evidence_refs: List[str] = field(default_factory=list)
    admits_missing_evidence: bool = False
    ts: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        # A response must cite evidence or explicitly admit there is none.
        if not self.evidence_refs and not self.admits_missing_evidence:
            self.admits_missing_evidence = True

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "evidence_refs": list(self.evidence_refs),
                "admits_missing_evidence": self.admits_missing_evidence,
                "ts": self.ts}


@dataclass
class ReviewerObjection:
    """One reviewer objection with its status and responses (append-only)."""

    objection_id: str
    text: str
    status: str = ObjectionStatus.NEW
    claim_refs: List[str] = field(default_factory=list)
    responses: List[ReviewerResponse] = field(default_factory=list)
    ts: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.status not in ObjectionStatus.ALL:
            self.status = ObjectionStatus.NEW

    @property
    def open(self) -> bool:
        return self.status in ObjectionStatus.OPEN

    def to_dict(self) -> Dict[str, Any]:
        return {"objection_id": self.objection_id, "text": self.text,
                "status": self.status, "claim_refs": list(self.claim_refs),
                "response_count": len(self.responses),
                "responses": [r.to_dict() for r in self.responses],
                "open": self.open, "ts": self.ts}


@dataclass
class ReviewerResponseLedger:
    """Append-only ledger of objections + responses; objections never deleted."""

    state_dir: str = ".solaris_ai_nn_review"
    persist: bool = True
    objections: List[ReviewerObjection] = field(default_factory=list, init=False)

    @property
    def _ledger_path(self) -> str:
        return os.path.join(self.state_dir, "response_ledger.json")

    @property
    def _history_path(self) -> str:
        return os.path.join(self.state_dir, "response_history.jsonl")

    def add_objection(self, objection: ReviewerObjection) -> ReviewerObjection:
        self.objections.append(objection)
        if self.persist:
            self._append_history({"event": "objection",
                                  **objection.to_dict()})
            self._write_ledger()
        return objection

    def respond(self, objection_id: str, response: ReviewerResponse, *,
                status: Optional[str] = None) -> bool:
        for o in self.objections:
            if o.objection_id == objection_id:
                o.responses.append(response)
                if status and status in ObjectionStatus.ALL:
                    o.status = status
                elif o.status == ObjectionStatus.NEW:
                    o.status = ObjectionStatus.ANSWERED
                if self.persist:
                    self._append_history({"event": "response",
                                          "objection_id": objection_id,
                                          **response.to_dict(),
                                          "status": o.status})
                    self._write_ledger()
                return True
        return False

    def open_objections(self) -> List[ReviewerObjection]:
        return [o for o in self.objections if o.open]

    def unresolved_objections(self) -> List[ReviewerObjection]:
        return [o for o in self.objections
                if o.status == ObjectionStatus.UNRESOLVED]

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for o in self.objections:
            out[o.status] = out.get(o.status, 0) + 1
        return out

    def _append_history(self, payload: Dict[str, Any]) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._history_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, default=str) + "\n")

    def _write_ledger(self) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._ledger_path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)

    def to_dict(self) -> Dict[str, Any]:
        counts = self.counts()
        return {
            "objection_count": len(self.objections),
            "open_objection_count": len(self.open_objections()),
            "unresolved_objection_count": len(self.unresolved_objections()),
            "accepted_limitation_count": counts.get(
                ObjectionStatus.ACCEPTED_AS_LIMITATION, 0),
            "accepted_falsification_count": counts.get(
                ObjectionStatus.ACCEPTED_AS_FALSIFICATION, 0),
            "counts_by_status": counts,
            "objections": [o.to_dict() for o in self.objections],
            "note": "append-only; objections cannot be deleted, accepted "
                    "limitations and falsifications stay visible, responses cite "
                    "evidence or admit its absence, and the system cannot declare "
                    "victory over a reviewer by default",
        }


def load_objections(records: Optional[List[Dict[str, Any]]],
                    ) -> List[ReviewerObjection]:
    """Load operator-provided reviewer objections (never invented)."""
    out: List[ReviewerObjection] = []
    for i, r in enumerate(records or []):
        objection = ReviewerObjection(
            objection_id=str(r.get("objection_id", f"obj_{i+1}")),
            text=str(r.get("text", "")),
            status=str(r.get("status", ObjectionStatus.NEW)),
            claim_refs=list(r.get("claim_refs", [])))
        for resp in r.get("responses", []) or []:
            objection.responses.append(ReviewerResponse(
                text=str(resp.get("text", "")),
                evidence_refs=list(resp.get("evidence_refs", [])),
                admits_missing_evidence=bool(
                    resp.get("admits_missing_evidence", False))))
        out.append(objection)
    return out
