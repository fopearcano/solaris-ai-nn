"""Failed/missing/falsified evidence is preserved through a runtime pass."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import ResearchCycleRuntime


def test_falsified_and_missing_preserved_in_ledger(tmp_path):
    rt = ResearchCycleRuntime(state_dir=str(tmp_path))
    rt.load_bundle({
        "research_baseline": {"baseline_status": "in_progress"},
        "implementation_intake": {"critical_safety_regression_count": 1},
        "falsification": {"falsified_claim_count": 2}})
    rt.run()
    st = rt.research_cycle_status()
    assert st["falsified_evidence_entry_count"] >= 1
    assert st["negative_evidence_entry_count"] >= 1
    assert st["missing_evidence_entry_count"] >= 1


def test_ledger_is_append_only(tmp_path):
    rt = ResearchCycleRuntime(state_dir=str(tmp_path))
    rt.load_bundle({"research_baseline": {"baseline_status": "validated"}})
    rt.run()
    assert rt.ledger.to_dict()["append_only"] is True


def test_blocked_evidence_recorded(tmp_path):
    # Validated baseline (stage != BLOCKED) but a falsified claim makes the
    # cycle blocked -- the runtime records a distinct blocked-evidence entry.
    rt = ResearchCycleRuntime(state_dir=str(tmp_path))
    rt.load_bundle({"research_baseline": {"baseline_status": "validated"},
                    "falsification": {"falsified_claim_count": 1}})
    res = rt.run()
    assert res["blocked"] is True
    counts = rt.ledger.counts()
    assert counts.get("blocked_evidence", 0) >= 1
