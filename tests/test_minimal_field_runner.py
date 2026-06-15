"""MinimalFieldOrganismRunner: prepares; bounded; read-only; no hardware."""

from __future__ import annotations

import inspect

from solaris_ai_nn.organismic_demo import (
    MinimalFieldOrganismRunner,
    OrganismicDemoConfig,
)
from solaris_ai_nn.organismic_demo import field_runner


def _runner(tmp_path, **kw):
    return MinimalFieldOrganismRunner(
        state_dir=str(tmp_path / "demo"),
        config=OrganismicDemoConfig(ticks=40, max_events_total=120, seed=7),
        **kw)


def test_runner_prepares(tmp_path):
    runner = _runner(tmp_path)
    assert runner.prepare() is True
    assert runner.runtime is not None
    assert len(runner.runtime.feeders) == 7


def test_bounded_run_completes(tmp_path):
    runner = _runner(tmp_path)
    result = runner.run()
    assert result["refused"] is False
    assert result["ticks_run"] <= 40
    assert runner.runtime.events_ingested <= 120


def test_fixture_files_read_through_adapters(tmp_path):
    runner = _runner(tmp_path)
    runner.run()
    # Receptors only exist if envelopes were read via the adapter path.
    assert runner.runtime.receptors
    assert runner.runtime.events_ingested > 0


def test_no_hardware_network_shell_in_source():
    src = inspect.getsource(field_runner)
    assert "subprocess" not in src
    assert "os.system" not in src
    assert "import socket" not in src
    assert "urllib" not in src


def test_changed_perception_probe_runs(tmp_path):
    runner = _runner(tmp_path)
    runner.run()
    assert runner.probe_result is not None
    assert 0.0 <= runner.probe_result.changed_perception_score <= 1.0
