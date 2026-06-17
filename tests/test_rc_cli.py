"""RC CLI: all six commands work; strict mode returns nonzero on blockers."""

from __future__ import annotations

from _tester_rc_helpers import seed_ready_state

from solaris_ai_nn.cli import main


def test_tester_rc_command(tmp_path):
    base = str(tmp_path / "rc")
    seed_ready_state(base)
    assert main(["tester-rc", "--tester-state-dir", base]) == 0


def test_tester_rc_manifest_command(tmp_path):
    assert main(["tester-rc-manifest", "--tester-state-dir",
                 str(tmp_path / "rc")]) == 0


def test_tester_rc_readiness_command(tmp_path):
    assert main(["tester-rc-readiness", "--tester-state-dir",
                 str(tmp_path / "rc")]) == 0


def test_tester_rc_docs_command(tmp_path):
    assert main(["tester-rc-docs", "--tester-state-dir",
                 str(tmp_path / "rc")]) == 0


def test_tester_rc_bundle_command(tmp_path):
    assert main(["tester-rc-bundle", "--tester-state-dir",
                 str(tmp_path / "rc")]) == 0


def test_tester_rc_checklist_command(tmp_path):
    assert main(["tester-rc-checklist", "--tester-state-dir",
                 str(tmp_path / "rc")]) == 0


def test_strict_returns_nonzero_on_blockers(tmp_path):
    # Fresh under-prepared state -> blockers -> strict nonzero.
    rc = main(["tester-rc", "--tester-state-dir", str(tmp_path / "empty"),
               "--strict"])
    assert rc == 2


def test_strict_ready_returns_zero(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    assert main(["tester-rc", "--tester-state-dir", base, "--strict"]) == 0
