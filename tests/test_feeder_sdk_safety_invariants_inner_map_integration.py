"""Feeder SDK <-> Safety invariants + Inner MAP integration."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph
from solaris_ai_nn.safety_invariants.registry import SafetyInvariantRegistry


def test_invariants_registered():
    reg = SafetyInvariantRegistry()
    methods = {inv.check_method for inv in reg.all_invariants()}
    for check in ("check_feeder_sdk_no_control", "check_feeder_sdk_no_decode",
                  "check_feeder_sdk_text_not_command",
                  "check_feeder_sdk_invalid_quarantined"):
        assert check in methods


def test_feeder_invariants_apply_to_module():
    reg = SafetyInvariantRegistry()
    feeder = [inv for inv in reg.all_invariants()
              if "feeder_sdk" in inv.applies_to_modules]
    assert len(feeder) >= 4


def test_inner_map_model_has_feeder_sdk_field():
    assert InnerMapModel().feeder_sdk is None


def test_inner_map_includes_feeder_sdk_state():
    observer = InnerMapObserver(feeder_sdk={
        "feeder_sdk_enabled": True, "available_feeder_count": 10,
        "active_feeder_output_count": 2, "invalid_feeder_event_count": 0})
    model = observer.update()
    assert model.feeder_sdk is not None
    assert model.feeder_sdk["available_feeder_count"] == 10


def test_state_graph_has_feeder_sdk_nodes():
    g = build_default_state_graph()
    for node in ("FeederSDKEnvelope", "EnvelopeWriter", "EnvelopeValidator",
                 "FeederReplay", "PrivacyFilter", "FeederBlueprint",
                 "FeederPackManifest", "FeederMonitor",
                 "FeederSDKSafetyValidator"):
        assert node in g.nodes
