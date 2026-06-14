"""Pilot-2 config: defaults, provenance, read-only environmental roots."""

from __future__ import annotations

import pytest

from solaris_ai_nn.pilot2 import (
    Pilot2Authority,
    Pilot2Config,
    Pilot2Mode,
    Pilot2SourceMode,
)


def test_defaults_plan_only(tmp_path):
    cfg = Pilot2Config(base_dir=str(tmp_path))
    assert cfg.mode == Pilot2Mode.PLAN_ONLY
    assert cfg.is_fixture_or_plan and not cfg.is_real_time
    assert not cfg.requires_governance


def test_provenance_required_by_default(tmp_path):
    assert Pilot2Config(base_dir=str(tmp_path)).provenance_required is True


def test_unknown_values_rejected(tmp_path):
    with pytest.raises(ValueError):
        Pilot2Config(mode="nope", base_dir=str(tmp_path))
    with pytest.raises(ValueError):
        Pilot2Config(authority="nope", base_dir=str(tmp_path))
    with pytest.raises(ValueError):
        Pilot2Config(source_mode="nope", base_dir=str(tmp_path))


def test_real_modes_require_governance(tmp_path):
    for mode in (Pilot2Mode.READ_ONLY_24H, Pilot2Mode.READ_ONLY_7D,
                 Pilot2Mode.READ_ONLY_30D):
        cfg = Pilot2Config(mode=mode, base_dir=str(tmp_path))
        assert cfg.requires_governance and cfg.is_real_time
        assert cfg.required_scope


def test_source_modes_and_boundaries(tmp_path):
    mixed = Pilot2Config(source_mode=Pilot2SourceMode.MIXED_NURSERY_AND_MEMBRANE,
                         base_dir=str(tmp_path))
    assert mixed.uses_membrane and mixed.uses_nursery
    nursery = Pilot2Config(source_mode=Pilot2SourceMode.NURSERY_ONLY,
                           base_dir=str(tmp_path))
    assert nursery.uses_nursery and not nursery.uses_membrane


def test_root_approved(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    cfg = Pilot2Config(base_dir=str(tmp_path), input_roots=[str(root)])
    assert cfg.root_approved(str(root / "x.jsonl"))
    assert not cfg.root_approved("/etc/passwd")


def test_roundtrip(tmp_path):
    cfg = Pilot2Config(mode=Pilot2Mode.READ_ONLY_7D, base_dir=str(tmp_path))
    clone = Pilot2Config.from_dict(cfg.to_dict())
    assert clone.mode == cfg.mode and clone.source_mode == cfg.source_mode
