"""Post-pilot report: generated, ClaimGuard-scanned, decision included."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.post_pilot import PilotArtifactLoader, PostPilotReportBuilder


def _arts(tmp_path):
    base = tmp_path / "pilot1"
    state = tmp_path / "state"
    (base / "daily").mkdir(parents=True)
    state.mkdir()
    (base / "observability.jsonl").write_text(
        json.dumps({"kind": "metrics", "payload": {}}) + "\n")
    (base / "PILOT_REPORT.json").write_text(json.dumps(
        {"sections": {"run": {"mode": "developmental_simulated", "steps": 50},
                      "uptime_ratio": 0.98}, "claim_guard_safe": True}))
    (state / "developmental_state.json").write_text(
        json.dumps({"epoch": "infancy"}))
    return PilotArtifactLoader(str(base), str(state)).load(), str(base), \
        str(state)


def test_report_generated(tmp_path):
    arts, base, state = _arts(tmp_path)
    builder = PostPilotReportBuilder(base_dir=base, state_dir=state)
    analysis = builder.build_and_write(artifacts=arts)
    assert os.path.exists(analysis.report_paths["markdown"])
    assert os.path.exists(analysis.report_paths["json"])


def test_claim_guard_scans_report(tmp_path):
    arts, base, state = _arts(tmp_path)
    analysis = PostPilotReportBuilder(base_dir=base,
                                      state_dir=state).build(artifacts=arts)
    assert analysis.claim_guard_safe is True
    assert "does not, and cannot, demonstrate" in analysis.narrative


def test_decision_gate_included(tmp_path):
    arts, base, state = _arts(tmp_path)
    builder = PostPilotReportBuilder(base_dir=base, state_dir=state)
    analysis = builder.build_and_write(artifacts=arts)
    data = json.loads(open(analysis.report_paths["json"]).read())
    assert "decision_gate" in data["sections"]
    assert data["summary"]["phase2_recommendation"] is not None


def test_sections_complete(tmp_path):
    arts, base, state = _arts(tmp_path)
    analysis = PostPilotReportBuilder(base_dir=base,
                                      state_dir=state).build(artifacts=arts)
    sections = analysis._sections_cache
    for key in ("artifact_completeness", "baseline_comparison",
                "structural_change_evidence", "accumulation_vs_growth",
                "developmental_evidence_ledger", "regression_analysis",
                "trace_audit", "reproducibility_package", "decision_gate",
                "limitations"):
        assert key in sections
