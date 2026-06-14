"""Ops integration for the conscience runtime: incident types + warnings."""

from __future__ import annotations

from solaris_ai_nn.ops import incident as I
from solaris_ai_nn.ops.incident import Incident
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


def test_new_incident_types_registered():
    for t in (I.CONSCIENCE_CRITICAL_MODULE_UNAVAILABLE,
              I.CONSCIENCE_SCHEDULER_PHASE_FAILING,
              I.CONSCIENCE_BUS_OVERFLOW,
              I.CONSCIENCE_CHECKPOINT_FAILURE,
              I.CONSCIENCE_EMERGENCY_STOP_REQUESTED,
              I.CONSCIENCE_MODULE_BYPASS_ATTEMPT):
        assert t in I.INCIDENT_TYPES


def test_unknown_incident_type_rejected():
    try:
        Incident(type="not_a_type", severity="info", message="x")
        assert False
    except ValueError:
        pass


class _FakeConscience:
    def __init__(self, **summary):
        self._summary = {
            "missing_modules": [], "degraded_modules": [],
            "bus_message_count": 0, "step_count": 1, "stopped": False,
        }
        self._summary.update(summary)
        self.emergency_requested = summary.get("emergency_requested", False)

    def summary(self):
        return dict(self._summary)

    def snapshot(self):
        return {"spine": {"status_counts": self._summary.get(
            "status_counts", {})}, "safety": {"rejected_count": 0}}


class _FakeRunner:
    def __init__(self, conscience):
        self.conscience = conscience


def _supervisor(tmp_path):
    return OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "state"),
            artifact_dir=str(tmp_path / "ops"), seed=5),
        registry=RunRegistry(tmp_path / "registry.json"))


def _types(sup):
    return {row["type"] for row in sup.incidents.list_incidents()}


def test_critical_module_unavailable_is_recorded(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _FakeRunner(_FakeConscience(
        missing_modules=["governance"]))
    sup._supervise()
    assert I.CONSCIENCE_CRITICAL_MODULE_UNAVAILABLE in _types(sup)


def test_emergency_stop_request_is_recorded(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _FakeRunner(_FakeConscience(emergency_requested=True))
    sup._supervise()
    assert I.CONSCIENCE_EMERGENCY_STOP_REQUESTED in _types(sup)


def test_healthy_conscience_records_no_conscience_incident(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _FakeRunner(_FakeConscience())
    sup._supervise()
    conscience_incidents = {t for t in _types(sup)
                            if t.startswith("conscience_")}
    assert conscience_incidents == set()
