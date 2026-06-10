"""Tests for the SolarisNNSidecar against the fake Conscience."""

from __future__ import annotations

import pytest

from solaris_ai_nn.experiments.solaris_sidecar_observation import (
    FakeConscience,
    Reaction,
    Stimulus,
)
from solaris_ai_nn.integration.conscience_sidecar import SolarisNNSidecar


def _attached(observe_only=True):
    conscience = FakeConscience()
    sidecar = SolarisNNSidecar(observe_only=observe_only,
                               vocabulary=["light", "noise", "food"], seed=3)
    sidecar.attach(conscience)
    sidecar.start()
    return conscience, sidecar


def test_sidecar_attaches_and_reports_compatibility():
    conscience, sidecar = _attached()
    assert sidecar.report is not None
    assert sidecar.report.is_compatible()
    assert sidecar.state.attached is True
    assert sidecar.state.compatibility_level == "sidecar_ready"


def test_sidecar_processes_fake_signals_and_suggests():
    conscience, sidecar = _attached()
    for i in range(6):
        conscience.bus.publish(Stimulus(payload="light", intensity=0.7))
        conscience.bus.publish(Reaction(valence=1.0))
    state = sidecar.state
    assert state.signals_observed == 12
    assert state.suggestions_produced == 6
    assert state.reactions_learned == 6
    assert len(sidecar.mirror) == 12
    assert sidecar.bridge.last_suggestion() is not None


def test_sidecar_never_calls_conscience_act_or_death():
    conscience, sidecar = _attached()
    for _ in range(10):
        conscience.bus.publish(Stimulus(payload="noise", intensity=0.6))
    sidecar.stop()
    sidecar.detach()
    # The sidecar observed and suggested but never drove the conscience.
    assert conscience.stimulate_calls == 0
    assert conscience.react_calls == 0
    assert conscience.death_calls == 0


def test_sidecar_detaches_safely_and_stops_observing():
    conscience, sidecar = _attached()
    conscience.bus.publish(Stimulus(payload="light"))
    assert sidecar.state.signals_observed == 1
    sidecar.detach()
    conscience.bus.publish(Stimulus(payload="light"))
    assert sidecar.state.signals_observed == 1  # nothing after detach
    # Re-attach works after a clean detach.
    sidecar.attach(conscience)
    sidecar.start()
    conscience.bus.publish(Stimulus(payload="light"))
    assert sidecar.state.signals_observed == 1  # fresh connector state


def test_attach_rejects_incompatible_runtime():
    class Nothing:
        pass

    sidecar = SolarisNNSidecar()
    with pytest.raises(ValueError):
        sidecar.attach(Nothing())


def test_start_requires_attach():
    sidecar = SolarisNNSidecar()
    with pytest.raises(RuntimeError):
        sidecar.start()


def test_snapshot_and_healthcheck():
    conscience, sidecar = _attached()
    conscience.bus.publish(Stimulus(payload="food"))
    snap = sidecar.snapshot()
    assert snap["started"] is True
    assert snap["integration"]["action_authority"] is False
    assert snap["integration"]["substrate_type"] == "esn"
    health = sidecar.healthcheck()
    assert health["healthy"] is True
    assert health["error_count"] == 0


def test_persist_writes_integration_files(tmp_path):
    conscience, sidecar = _attached()
    conscience.bus.publish(Stimulus(payload="light"))
    paths = sidecar.persist(tmp_path / "state")
    from pathlib import Path
    assert Path(paths["integration_state"]).exists()
    assert Path(paths["suggestions"]).exists()
    assert Path(paths["mirrored_signals"]).exists()


def test_observer_includes_sidecar_integration_state():
    conscience, sidecar = _attached()
    conscience.bus.publish(Stimulus(payload="light"))
    from solaris_ai_nn.inner_map.observer import InnerMapObserver

    model = InnerMapObserver(bridge=sidecar.bridge, sidecar=sidecar).update()
    assert model.integration is not None
    assert model.integration["attached"] is True
    assert model.integration["action_authority"] is False
    assert model.integration["compatibility_level"] == "sidecar_ready"
