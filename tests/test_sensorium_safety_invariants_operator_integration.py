"""Plural sensorium <-> safety invariants / operator console integration."""

from __future__ import annotations

from solaris_ai_nn.operator_console import ProfileCatalog
from solaris_ai_nn.safety_invariants.registry import SafetyInvariantRegistry


def test_invariants_registered():
    reg = SafetyInvariantRegistry()
    methods = {inv.check_method for inv in reg.all_invariants()}
    for check in ("check_sensorium_no_hardware", "check_sensorium_no_network",
                  "check_sensorium_no_source_modification",
                  "check_sensorium_text_not_command",
                  "check_sensorium_bounded_polling"):
        assert check in methods


def test_sensorium_invariants_apply_to_module():
    reg = SafetyInvariantRegistry()
    sensorium_invs = [inv for inv in reg.all_invariants()
                      if "plural_sensorium" in inv.applies_to_modules]
    assert len(sensorium_invs) >= 5


def test_operator_console_lists_sensorium_profiles():
    catalog = ProfileCatalog()
    ids = {e.profile_id for e in catalog.entries()}
    assert "plural_sensorium_fixture_short" in ids
    assert "plural_sensorium_rf_fixture_short" in ids
    # They are attributed to the plural_sensorium source package.
    entry = catalog.get("plural_sensorium_fixture_short")
    assert entry.source_package == "plural_sensorium"
    assert entry.external_authority is False
