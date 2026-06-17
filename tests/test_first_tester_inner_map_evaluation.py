"""First tester integration: Inner MAP record/field, evaluation metrics."""

from __future__ import annotations

from _first_tester_helpers import run_protocol

from solaris_ai_nn.inner_map.model import InnerMapModel


def test_inner_map_field_and_record(tmp_path):
    rt = run_protocol(str(tmp_path / "p"))
    rec = rt.inner_map_record()
    model = InnerMapModel()
    model.first_tester_protocol = rec
    d = model.to_dict()
    assert d["first_tester_protocol"]["first_tester_protocol_run_id"] == \
        rt.run_id
    assert d["first_tester_protocol"]["local_only"] is True


def test_inner_map_record_has_paths(tmp_path):
    rt = run_protocol(str(tmp_path / "p"))
    rec = rt.inner_map_record()
    assert rec["session_script_path"]
    assert rec["handoff_guide_path"]


def test_evaluation_metrics_computed(tmp_path):
    from solaris_ai_nn.evaluation.metrics import (
        first_tester_protocol_metrics as ftp_metrics,
    )
    rt = run_protocol(str(tmp_path / "p"))
    m = ftp_metrics(rt.protocol_status())
    assert m["present"] is True
    assert m["first_tester_protocol_run_count"] == 1
    assert m["runs_session"] is False
    assert m["is_consciousness_or_personhood"] is False


def test_evaluation_metrics_absent():
    from solaris_ai_nn.evaluation.metrics import (
        first_tester_protocol_metrics as ftp_metrics,
    )
    assert ftp_metrics(None) == {"present": False}
