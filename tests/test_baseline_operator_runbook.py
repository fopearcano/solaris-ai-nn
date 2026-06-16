"""Baseline operator runbook: generated, stop conditions, no command execution."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import build_operator_runbook


def test_runbook_generated():
    rb = build_operator_runbook(baseline_version_id="rb_v1", status="validated")
    d = rb.to_dict()
    assert d["step_count"] >= 8
    sections = {s["section"] for s in d["steps"]}
    assert "safety boundaries" in sections
    assert "how to run tests" in sections
    assert "rollback guidance" in sections


def test_stop_conditions_present():
    rb = build_operator_runbook(baseline_version_id="rb_v1", status="validated")
    assert rb.stop_conditions
    joined = " ".join(rb.stop_conditions).lower()
    assert "safety" in joined
    assert "critical limitation" in joined


def test_no_command_execution():
    rb = build_operator_runbook(baseline_version_id="rb_v1", status="validated")
    d = rb.to_dict()
    assert d["executes_commands"] is False
    md = rb.render_markdown()
    assert "executes no command" in md


def test_render_includes_stop_conditions_section():
    rb = build_operator_runbook(baseline_version_id="rb_v1",
                                status="validated_with_warnings")
    md = rb.render_markdown()
    assert "Stop conditions" in md
