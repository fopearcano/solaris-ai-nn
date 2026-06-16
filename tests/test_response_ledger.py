"""Response ledger: append-only, accepted limitations kept, unresolved visible."""

from __future__ import annotations

import os

from solaris_ai_nn.independent_review import (
    ObjectionStatus,
    ReviewerObjection,
    ReviewerResponse,
    ReviewerResponseLedger,
)


def test_objections_append_only(tmp_path):
    ledger = ReviewerResponseLedger(state_dir=str(tmp_path))
    ledger.add_objection(ReviewerObjection(objection_id="o1", text="overfit?"))
    ledger.add_objection(ReviewerObjection(objection_id="o2", text="replicate?"))
    assert ledger.to_dict()["objection_count"] == 2
    # There is no delete API; objections persist.
    assert not hasattr(ledger, "delete_objection")
    assert os.path.isfile(os.path.join(str(tmp_path), "response_history.jsonl"))


def test_accepted_limitations_preserved(tmp_path):
    ledger = ReviewerResponseLedger(state_dir=str(tmp_path))
    ledger.add_objection(ReviewerObjection(objection_id="o1", text="no live data"))
    ledger.respond("o1", ReviewerResponse(text="accepted", admits_missing_evidence=True),
                   status=ObjectionStatus.ACCEPTED_AS_LIMITATION)
    d = ledger.to_dict()
    assert d["accepted_limitation_count"] == 1
    assert d["objections"][0]["status"] == ObjectionStatus.ACCEPTED_AS_LIMITATION


def test_unresolved_objections_visible(tmp_path):
    ledger = ReviewerResponseLedger(state_dir=str(tmp_path))
    ledger.add_objection(ReviewerObjection(
        objection_id="o1", text="log accumulation?",
        status=ObjectionStatus.UNRESOLVED))
    assert ledger.to_dict()["unresolved_objection_count"] == 1
    assert len(ledger.unresolved_objections()) == 1


def test_response_must_cite_or_admit(tmp_path):
    ledger = ReviewerResponseLedger(state_dir=str(tmp_path))
    ledger.add_objection(ReviewerObjection(objection_id="o1", text="x"))
    # A response with no evidence refs auto-admits missing evidence.
    ledger.respond("o1", ReviewerResponse(text="no evidence yet"))
    resp = ledger.objections[0].responses[0]
    assert resp.admits_missing_evidence is True


def test_no_default_victory(tmp_path):
    ledger = ReviewerResponseLedger(state_dir=str(tmp_path))
    ledger.add_objection(ReviewerObjection(objection_id="o1", text="x"))
    # A new objection is open, not auto-resolved in the project's favour.
    assert ledger.to_dict()["open_objection_count"] == 1
