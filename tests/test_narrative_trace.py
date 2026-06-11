"""Tests for the narrative trace."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.ego.narrative_trace import TEMPLATES, NarrativeTrace


def test_narrative_event_references_evidence():
    trace = NarrativeTrace()
    event = trace.add("perspective_shift",
                      evidence=["context:latent_mode=replay"],
                      mode="latent_offline_replay",
                      reason="latent offline processing")
    assert event.evidence_refs == ["context:latent_mode=replay"]
    assert "entered latent_offline_replay mode" in event.text
    with pytest.raises(ValueError):
        trace.add("perspective_shift", evidence=[], mode="x", reason="y")
    with pytest.raises(ValueError):
        trace.add("not_a_template", evidence=["e"])


def test_no_first_person_claims():
    trace = NarrativeTrace()
    for template_id, template in TEMPLATES.items():
        lowered = template.lower()
        assert not lowered.startswith("i "), template_id
        assert " i " not in f" {lowered} ", template_id
    # Values that would smuggle first-person wording are refused.
    with pytest.raises(ValueError):
        trace.add("identity_uncertain", evidence=["e"],
                  reason="I want to continue")


def test_jsonl_persistence_works(tmp_path):
    trace = NarrativeTrace(state_dir=tmp_path)
    trace.add("run_started", evidence=["lifecycle:birth"], run_id="r1")
    trace.add("checkpoint_saved", evidence=["checkpoint:42"], step=42)
    path = tmp_path / "narrative_trace.jsonl"
    assert path.exists()
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 2
    assert rows[0]["template_id"] == "run_started"
    assert rows[1]["text"] == "A checkpoint was saved at step 42."
    assert trace.rows_written == 2


def test_story_and_bounds():
    trace = NarrativeTrace(max_events=3)
    for step in range(5):
        trace.add("checkpoint_saved", evidence=[f"checkpoint:{step}"],
                  step=step)
    assert len(trace.events) == 3  # bounded
    story = trace.as_story()
    assert story.count("checkpoint was saved") == 3
    snapshot = trace.snapshot()
    assert "no first-person" in snapshot["note"]
