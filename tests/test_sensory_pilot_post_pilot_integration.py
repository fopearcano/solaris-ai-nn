"""Sensory <-> Pilot / Post-Pilot: source summary and nursery-vs-membrane."""

from __future__ import annotations

from solaris_ai_nn.sensory_membrane import (
    SensoryMembraneRuntime,
    SensorySourceConfig,
)


def _membrane(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    (root / "e.jsonl").write_text('{"a":1}\n{"a":2}\n')
    rt = SensoryMembraneRuntime(
        state_dir=str(tmp_path / "state"), allowed_input_roots=[str(root)],
        enabled=True, simulated_sources_only=False,
        real_read_only_sources_enabled=True)
    rt.add_source(SensorySourceConfig(source_id="j", source_type="jsonl_file",
                                      path=str(root / "e.jsonl"),
                                      enabled=True))
    rt.initialize()
    rt.run_bounded(max_polls=2)
    return rt


def test_membrane_summary_distinguishes_real_vs_simulated(tmp_path):
    rt = _membrane(tmp_path)
    summary = rt.summary()
    # The membrane summary carries the source counts a pilot report can embed.
    assert summary["source_count"] == 1
    assert summary["read_only"] is True
    prov = rt.snapshot()["provenance"]
    assert prov["real_count"] >= 1  # real read-only source, not simulated


def test_pilot_report_can_embed_source_summary(tmp_path):
    from solaris_ai_nn.pilot1 import PilotConfig, PilotReportBuilder

    rt = _membrane(tmp_path)
    cfg = PilotConfig(base_dir=str(tmp_path / "pilot1"))
    builder = PilotReportBuilder(base_dir=str(tmp_path / "pilot1"))
    report = builder.build(config=cfg,
                           extra={"sensory_source_summary": rt.summary()})
    # The pilot report accepts arbitrary extra sections without crashing.
    assert report.report_id


def test_post_pilot_can_note_membrane_mode(tmp_path):
    # A nursery-only run vs a membrane run is distinguished by metadata the
    # post-pilot baseline comparator can read.
    from solaris_ai_nn.post_pilot import BaselineComparator

    cmp = BaselineComparator().compare_dicts(
        "nursery_only", {"structural_change_score": 0.1},
        "membrane_run", {"structural_change_score": 0.2})
    assert "structural_change_score" in cmp.deltas
