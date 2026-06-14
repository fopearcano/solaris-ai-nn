"""Module lifecycle: bounded transitions, degraded/failed, safe shutdown."""

from __future__ import annotations

from solaris_ai_nn.conscience import ModuleLifecycleManager, ModuleLifecycleState


def test_initial_state_reflects_availability():
    m = ModuleLifecycleManager()
    m.initial("a", available=True)
    m.initial("b", available=False)
    assert m.states["a"] == ModuleLifecycleState.REGISTERED
    assert m.states["b"] == ModuleLifecycleState.UNAVAILABLE


def test_happy_path_transitions():
    m = ModuleLifecycleManager()
    m.initial("a", available=True)
    for t in ("configure", "initialize", "start"):
        m.transition("a", t)
    assert m.states["a"] == ModuleLifecycleState.RUNNING
    assert "a" in m.running()


def test_unavailable_module_only_reregisterable():
    m = ModuleLifecycleManager()
    m.initial("a", available=False)
    # Starting an unavailable module is a no-op (stays unavailable).
    assert m.transition("a", "start") == ModuleLifecycleState.UNAVAILABLE
    assert m.transition("a", "register") == ModuleLifecycleState.REGISTERED


def test_unknown_transition_raises():
    m = ModuleLifecycleManager()
    m.initial("a", available=True)
    try:
        m.transition("a", "teleport")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_degraded_and_failed_listing():
    m = ModuleLifecycleManager()
    for name in ("a", "b"):
        m.initial(name, available=True)
    m.mark_degraded("a", "slow")
    m.fail("b", "boom")
    assert m.degraded() == ["a"]
    assert m.failed() == ["b"]


def test_safe_shutdown_all_stops_running():
    m = ModuleLifecycleManager()
    m.initial("a", available=True)
    m.transition("a", "start")
    m.safe_shutdown_all("end")
    assert m.states["a"] == ModuleLifecycleState.STOPPED


def test_snapshot_shape():
    m = ModuleLifecycleManager()
    m.initial("a", available=True)
    snap = m.snapshot()
    assert "states" in snap and "running" in snap
