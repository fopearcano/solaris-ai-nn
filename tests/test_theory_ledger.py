"""Theory ledger: versioned revisions, archived challenged/falsified, not proof."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import (
    TheoryLedger,
    TheoryStatement,
    TheoryStatus,
)


def test_theory_statement_versioned():
    ledger = TheoryLedger()
    ledger.add(TheoryStatement(theory_id="t1", area="semiogenesis",
                               text="signs form", status="working_hypothesis"))
    ledger.revise("t1", text="signs may form but parser-equivalent",
                  status=TheoryStatus.CHALLENGED,
                  counterevidence_refs=["passive_parser"])
    stmt = ledger.get("t1")
    assert stmt.status == TheoryStatus.CHALLENGED
    assert stmt.revisions  # prior version preserved
    assert stmt.revisions[0].status == TheoryStatus.WORKING_HYPOTHESIS


def test_challenged_and_falsified_preserved():
    ledger = TheoryLedger()
    ledger.add(TheoryStatement(theory_id="t1", area="x", text="a"))
    ledger.add(TheoryStatement(theory_id="t2", area="y", text="b",
                               status=TheoryStatus.FALSIFIED))
    ledger.revise("t1", text="a'", status=TheoryStatus.CHALLENGED)
    d = ledger.to_dict()
    assert d["challenged_count"] == 1
    assert d["falsified_count"] == 1
    assert all(s["archived"] for s in d["statements"]
               if s["status"] in (TheoryStatus.CHALLENGED,
                                   TheoryStatus.FALSIFIED))


def test_theory_is_not_proof():
    stmt = TheoryStatement(theory_id="t1", area="x", text="a")
    assert stmt.is_proof is False
    assert stmt.to_dict()["is_proof"] is False
    assert "not proof" in TheoryLedger().to_dict()["note"]
