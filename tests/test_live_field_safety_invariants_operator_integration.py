"""Live field <-> Safety invariants + Operator console integration."""

from __future__ import annotations

from solaris_ai_nn.operator_console import ProfileCatalog
from solaris_ai_nn.safety_invariants.registry import SafetyInvariantRegistry


def test_invariants_registered():
    reg = SafetyInvariantRegistry()
    methods = {inv.check_method for inv in reg.all_invariants()}
    for check in ("check_live_no_feeder_autostart",
                  "check_live_no_source_modification", "check_live_no_network",
                  "check_live_text_not_command",
                  "check_live_bounded_and_governed"):
        assert check in methods


def test_live_invariants_apply_to_module():
    reg = SafetyInvariantRegistry()
    live = [inv for inv in reg.all_invariants()
            if "live_field" in inv.applies_to_modules]
    assert len(live) >= 5


def test_operator_console_shows_live_field_status():
    catalog = ProfileCatalog()
    ids = {e.profile_id for e in catalog.entries()}
    assert "live_field_preflight" in ids
    assert "live_field_short_governed" in ids
    entry = catalog.get("live_field_preflight")
    assert entry.source_package == "live_field"
    assert entry.external_authority is False
