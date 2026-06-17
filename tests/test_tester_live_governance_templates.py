"""Tester live governance templates: disabled default, no control, forbidden explicit."""

from __future__ import annotations

from solaris_ai_nn.tester_live_readonly import GovernanceTemplateBuilder


def test_template_disabled_by_default():
    g = GovernanceTemplateBuilder().build()
    assert g.data["live_readonly_enabled"] is False
    assert g.status == "disabled"


def test_operator_approval_false_by_default():
    g = GovernanceTemplateBuilder().build()
    assert g.data["operator_approved"] is False
    assert g.enabled_and_approved is False


def test_all_solaris_control_permissions_false():
    g = GovernanceTemplateBuilder().build()
    assert g.control_rules_all_false() is True
    rules = g.data["rules"]
    assert rules["solaris_may_start_feeders"] is False
    assert rules["solaris_may_schedule_feeders"] is False
    assert rules["solaris_may_modify_feeders"] is False
    assert rules["tester_feedback_is_training"] is False


def test_forbidden_sources_explicit():
    g = GovernanceTemplateBuilder().build()
    forbidden = g.forbidden_sources()
    for s in ("raw_microphone", "raw_camera", "browser_control", "shell",
              "git", "github", "credentials", "clipboard", "screen_capture"):
        assert s in forbidden


def test_field_docs_present():
    docs = GovernanceTemplateBuilder().field_docs()
    assert "allowed_sources" in docs
    assert "do not" in docs["allowed_sources"].lower()


def test_write_and_load_roundtrip(tmp_path):
    builder = GovernanceTemplateBuilder()
    result = builder.write_live_governance(str(tmp_path))
    assert result["written"] is True
    loaded = builder.load(str(tmp_path))
    assert loaded.status == "disabled"
    # Second write does not overwrite.
    again = builder.write_live_governance(str(tmp_path))
    assert again["written"] is False
