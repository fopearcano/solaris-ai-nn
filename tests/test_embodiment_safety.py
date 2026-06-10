"""Tests for the embodiment safety layer."""

from __future__ import annotations

from solaris_ai_nn.embodiment.safety import EmbodimentSafety


def test_validates_safe_simulated_action():
    safety = EmbodimentSafety()
    assert safety.is_safe("move_north")
    assert safety.is_safe("rest")
    assert "safe simulated action" in safety.explain("look")


def test_rejects_unknown_action():
    safety = EmbodimentSafety()
    report = safety.validate_action("teleport_home")
    assert not report.safe
    assert any("outside the declared action space" in v for v in report.violations)


def test_rejects_real_world_action_mock():
    safety = EmbodimentSafety()
    for bad in ("send_http_request", "open_browser_click", "run_subprocess",
                "os_system_call", "robot_motor_forward", "file_write_secret"):
        report = safety.validate_action(bad)
        assert not report.safe, bad
        assert any("real-world actuation is forbidden" in v
                   for v in report.violations), bad


def test_rejects_unbounded_simulation_without_flag():
    safety = EmbodimentSafety()
    report = safety.validate_action("move_north", {"unbounded": True})
    assert not report.safe
    assert any("explicit continuous flag" in v for v in report.violations)
    # Explicit flag allows it.
    assert safety.is_safe("move_north", {"unbounded": True,
                                         "explicitly_continuous": True})


def test_rejects_action_outside_simulation():
    safety = EmbodimentSafety()
    report = safety.validate_action("move_north", {"outside_simulation": True})
    assert not report.safe


def test_snapshot_declares_simulation_only_authority():
    snap = EmbodimentSafety().snapshot()
    assert snap["action_authority"] == "simulation-only"
    assert snap["real_world_actions"] == "forbidden"
