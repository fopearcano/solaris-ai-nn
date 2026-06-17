"""RC checklist: generated, tiers separated, missing required blocks."""

from __future__ import annotations

from _tester_rc_helpers import run_rc, seed_ready_state


def test_checklist_generated(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    c = rt.checklist.to_dict()
    assert c["item_count"] > 0
    sections = {i["section"] for i in c["items"]}
    assert any(s.startswith("A.") for s in sections)
    assert any(s.startswith("H.") for s in sections)


def test_tiers_separated(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    tiers = rt.checklist.to_dict()["by_tier"]
    assert "required" in tiers
    assert "optional" in tiers


def test_missing_required_blocks(tmp_path):
    rt = run_rc(str(tmp_path / "empty"))
    # Fresh state -> some required items missing -> checklist not passed.
    assert rt.checklist.passed is False
    assert rt.checklist.blocking_items


def test_ready_state_checklist_passes(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    rt = run_rc(base)
    # Required artifacts present; remaining items default to safe pass.
    assert rt.checklist.passed is True
