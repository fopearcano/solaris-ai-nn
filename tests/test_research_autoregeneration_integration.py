"""Research <-> Auto-regeneration: artifact bloat warning; no auto-repair."""

from __future__ import annotations

from solaris_ai_nn.ops import incident as I
from solaris_ai_nn.ops.run_manifest import OperationalRunManifest, RunMode
from solaris_ai_nn.ops.run_registry import RunRegistry
from solaris_ai_nn.ops.supervisor import OperationalSupervisor


class _Runner:
    def __init__(self, research):
        self.research_lab = research


def _supervisor(tmp_path):
    return OperationalSupervisor(
        manifest=OperationalRunManifest(
            mode=RunMode.BOUNDED, max_steps=10,
            state_dir=str(tmp_path / "s"), artifact_dir=str(tmp_path / "o"),
            seed=5),
        registry=RunRegistry(tmp_path / "r.json"))


def test_artifact_bloat_warning_created(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "artifact_growth_excessive": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert I.RESEARCH_ARTIFACT_GROWTH in types


def test_no_auto_repair_of_evidence():
    # The failure-triage analogue for research never auto-repairs: the effect
    # analyzer only classifies; there is no repair API on it.
    from solaris_ai_nn.research_lab import EffectAnalyzer

    ea = EffectAnalyzer()
    assert not hasattr(ea, "repair")
    assert not hasattr(ea, "auto_repair")


def test_metric_failure_warning(tmp_path):
    sup = _supervisor(tmp_path)
    sup._last_runner = _Runner({"enabled": True,
                                "metric_computation_failed": True})
    sup._supervise()
    types = {row["type"] for row in sup.incidents.list_incidents()}
    assert I.RESEARCH_METRIC_FAILED in types
