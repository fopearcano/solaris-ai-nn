"""Tests for the self-report builder."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.ego.self_report import EGO_LIMITATIONS, SelfReportBuilder
from solaris_ai_nn.governance.compliance import ClaimGuard


def _model(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1", "session_id": "s1",
                  "substrate_identity": "esn", "health_level": "ok",
                  "embodiment": {"energy": 6.0, "max_energy": 10.0}})
    model.classify_event({"source": "stream", "kind": "stream_line"})
    return model


def test_report_json_generated(tmp_path):
    builder = SelfReportBuilder(_model(tmp_path))
    data = json.loads(builder.to_json())
    for section in ("identity_anchors", "continuity_score",
                    "current_perspective", "boundary_status",
                    "classification_summary", "evidence_summary",
                    "attribution_summary", "body_schema",
                    "action_authority_status",
                    "unresolved_identity_warnings", "unknowns"):
        assert section in data["sections"], section
    for limitation in EGO_LIMITATIONS:
        assert limitation in data["limitations"]


def test_markdown_generated(tmp_path):
    md = SelfReportBuilder(_model(tmp_path)).to_markdown()
    assert md.startswith("# Self-model report")
    assert "Identity Anchors" in md
    assert "Action Authority Status" in md
    assert "Limitations" in md


def test_claim_guard_scans_report(tmp_path):
    builder = SelfReportBuilder(_model(tmp_path))
    paths = builder.save(tmp_path / "sr.json", tmp_path / "sr.md")
    assert paths["claim_guard"]["safe"] is True
    assert (tmp_path / "sr.md").exists()
    assert ClaimGuard().is_safe((tmp_path / "sr.md").read_text())


def test_forbidden_wording_blocked(tmp_path):
    model = _model(tmp_path)
    # Poison an identity warning with forbidden first-person wording; the
    # save must refuse to write anything.
    model.identity.identity_warnings.append("I am conscious of the gap")
    builder = SelfReportBuilder(model)
    with pytest.raises(ValueError, match="self-report blocked"):
        builder.save(tmp_path / "bad.json", tmp_path / "bad.md")
    assert not (tmp_path / "bad.md").exists()


def test_safe_wording_present(tmp_path):
    md = SelfReportBuilder(_model(tmp_path)).to_markdown()
    lowered = md.lower()
    assert "runtime continuity" in lowered
    assert "no personhood" in lowered or "not personhood" in lowered
    for forbidden in ("i am conscious", "i know myself", "i have a soul",
                      "i freely chose", "i am alive"):
        assert forbidden not in lowered
