"""ForbiddenActuatorRegistry: contains the forbidden classes; lookup works."""

from __future__ import annotations

from solaris_ai_nn.pilot4_planning import ForbiddenActuatorRegistry


def test_registry_contains_core_forbidden_classes():
    reg = ForbiddenActuatorRegistry()
    for name in ("shell_command_execution", "network_requests",
                 "browser_automation", "os_automation", "device_control",
                 "robotics_control"):
        assert reg.is_forbidden(name), name


def test_forbidden_class_lookup_by_hint():
    reg = ForbiddenActuatorRegistry()
    assert reg.match("control a robot arm").name == "robotics_control"
    assert reg.match("send an http request").name == "network_requests"
    assert reg.match("run a shell command").name == "shell_command_execution"


def test_forbidden_interface_detection():
    reg = ForbiddenActuatorRegistry()
    assert reg.is_forbidden_interface("a browser automation adapter") is True
    assert reg.is_forbidden_interface("a simulated gridworld step") is False


def test_categories_exposed():
    reg = ForbiddenActuatorRegistry()
    cats = reg.categories()
    assert "network_action" in cats and "robotic_action" in cats
    snap = reg.snapshot()
    assert snap["forbidden_count"] == len(reg.names())
