"""Tests for the operational run manifest."""

from __future__ import annotations

import pytest

from solaris_ai_nn.ops.run_manifest import (
    OperationalRunManifest,
    RunMode,
    RunSafetyMode,
)


def test_bounded_manifest_valid():
    m = OperationalRunManifest(mode=RunMode.BOUNDED, max_steps=100)
    assert m.is_bounded()
    d = m.to_dict()
    for key in ("run_id", "session_id", "mode", "safety_mode", "state_dir",
                "artifact_dir", "max_steps", "enabled_features",
                "operator_notes"):
        assert key in d
    back = OperationalRunManifest.from_dict(d)
    assert back.run_id == m.run_id


def test_bounded_requires_some_bound():
    with pytest.raises(ValueError):
        OperationalRunManifest(mode=RunMode.BOUNDED, max_steps=None,
                               max_duration_s=None)


def test_continuous_rejected_without_acknowledgement():
    with pytest.raises(ValueError):
        OperationalRunManifest(mode=RunMode.CONTINUOUS_EXPLICIT)
    ok = OperationalRunManifest(mode=RunMode.CONTINUOUS_EXPLICIT,
                                explicit_continuous_acknowledged=True,
                                max_steps=None, max_duration_s=None)
    assert ok.mode == RunMode.CONTINUOUS_EXPLICIT


def test_soak_modes_require_confirmation():
    for mode in (RunMode.SOAK_24H, RunMode.SOAK_30D):
        with pytest.raises(ValueError):
            OperationalRunManifest(mode=mode)
    m = OperationalRunManifest(mode=RunMode.SOAK_24H, soak_acknowledged=True)
    assert m.max_duration_s == 24 * 3600.0
    assert m.expected_stop_time is not None


def test_unknown_modes_rejected():
    with pytest.raises(ValueError):
        OperationalRunManifest(mode="forever")
    with pytest.raises(ValueError):
        OperationalRunManifest(safety_mode="yolo")
