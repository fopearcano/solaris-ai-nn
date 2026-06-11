"""Tests for the world-model report builder."""

from __future__ import annotations

import json

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.signals import canonical as C
from solaris_ai_nn.world_model.builder import WorldModelBuilder
from solaris_ai_nn.world_model.reports import WorldModelReportBuilder


def _builder():
    builder = WorldModelBuilder()
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=3)
    for i in range(25):
        stim = C.Stimulus(payload=f"p{i % 3}", intensity=0.5)
        result = bridge.process(stim)
        builder.update_from_signal(stim, result)
        builder.update_from_reaction(result["suggested_action"],
                                     1.0 if i % 2 else -0.5)
    builder.update_from_trace(bridge.trace)
    return builder


def test_markdown_report_generated(tmp_path):
    report = WorldModelReportBuilder(builder=_builder())
    md = report.to_markdown()
    assert md.startswith("# World model report")
    for heading in ("Graph Summary", "Node Counts By Type",
                    "Edge Counts By Type", "Strongest Associations",
                    "Top Causal Candidates", "Unknown Nodes",
                    "Context Distribution", "Predictions",
                    "Pruning Subtraction"):
        assert heading in md, heading
    data = json.loads(report.to_json())
    assert data["sections"]["graph_summary"]["nodes"] > 1


def test_claim_guard_scans_report(tmp_path):
    report = WorldModelReportBuilder(builder=_builder())
    paths = report.save(tmp_path / "wm.json", tmp_path / "wm.md")
    assert paths["claim_guard"]["safe"] is True
    md = (tmp_path / "wm.md").read_text()
    assert "Claim Guard Warnings" not in md


def test_limitations_included():
    md = WorldModelReportBuilder(builder=_builder()).to_markdown()
    assert "Limitations and Unknowns" in md
    assert "not constitute" in md or "does not constitute" in md
    assert "not proven causation" in md
    assert "never treated as real observation" in md
    assert "never execute actions" in md
