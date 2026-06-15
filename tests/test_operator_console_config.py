"""OperatorConsoleConfig: safe defaults; no authority/network/shell; bounds."""

from __future__ import annotations

import pytest

from solaris_ai_nn.operator_console import (
    ConsoleAuthority,
    ConsoleMode,
    OperatorConsoleConfig,
)


def test_default_inspect_only(tmp_path):
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"))
    assert cfg.mode == ConsoleMode.INSPECT_ONLY


def test_real_world_authority_false(tmp_path):
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"),
                                real_world_authority=True)
    # It is forced off regardless of the constructor argument.
    assert cfg.real_world_authority is False
    assert cfg.to_dict()["real_world_authority"] is False


def test_network_and_shell_disabled(tmp_path):
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"),
                                network_enabled=True, shell_enabled=True)
    assert cfg.network_enabled is False
    assert cfg.shell_enabled is False


def test_forbidden_external_authority_rejected(tmp_path):
    with pytest.raises(ValueError):
        OperatorConsoleConfig(state_dir=str(tmp_path / "op"),
                              authority=ConsoleAuthority.FORBIDDEN_EXTERNAL)


def test_invalid_paths_blocked(tmp_path):
    # An export dir outside the approved roots is rejected.
    with pytest.raises(ValueError):
        OperatorConsoleConfig(state_dir=str(tmp_path / "op"),
                              export_dir="/etc/solaris_escape")


def test_dirs_inside_state_root(tmp_path):
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"))
    assert cfg.artifact_dir.startswith(cfg.state_dir)
    assert cfg.report_dir.startswith(cfg.state_dir)
    assert cfg.export_dir.startswith(cfg.state_dir)
