"""Soak runtime: bounded, calls engine, checkpoints/packets, no daemon/control."""

from __future__ import annotations

import inspect

from solaris_ai_nn.developmental_soak import DevelopmentalSoakRuntime
from solaris_ai_nn.developmental_soak import soak_runtime


def test_bounded_invocation(tmp_path):
    rt = DevelopmentalSoakRuntime(state_dir=str(tmp_path / "s"),
                                  stage="dry_run_2h", max_ticks=4,
                                  max_runtime_s=15.0)
    out = rt.run_stage("dry_run_2h")
    assert out["refused"] is False
    assert rt.ticks_run <= 4


def test_unbounded_refused(tmp_path):
    rt = DevelopmentalSoakRuntime(state_dir=str(tmp_path / "s"), max_ticks=0,
                                  max_runtime_s=0)
    assert rt.run_stage("dry_run_2h")["refused"] is True


def test_calls_developmental_runtime(tmp_path):
    rt = DevelopmentalSoakRuntime(state_dir=str(tmp_path / "s"),
                                  stage="developmental_soak_30d", max_ticks=4,
                                  max_runtime_s=15.0)
    rt.run_stage("developmental_soak_30d")
    from solaris_ai_nn.developmental_life import LongHorizonDevelopmentalRuntime

    assert isinstance(rt.dev_runtime, LongHorizonDevelopmentalRuntime)


def test_creates_checkpoint_and_daily_packet(tmp_path):
    rt = DevelopmentalSoakRuntime(state_dir=str(tmp_path / "s"),
                                  stage="developmental_soak_30d", max_ticks=6,
                                  max_runtime_s=20.0)
    rt.run_stage("developmental_soak_30d")
    st = rt.soak_status()
    assert st["checkpoint_count"] >= 1
    assert st["daily_packet_count"] >= 1


def test_status_disclaims_life(tmp_path):
    rt = DevelopmentalSoakRuntime(state_dir=str(tmp_path / "s"), max_ticks=2,
                                  max_runtime_s=10.0)
    st = rt.soak_status()
    assert st["is_biological_life"] is False
    assert st["is_consciousness_or_personhood"] is False


def test_no_daemon_or_control_in_source():
    src = inspect.getsource(soak_runtime)
    assert "while True" not in src
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "os.system" not in src
    assert "teaching_loop" not in src.lower()
