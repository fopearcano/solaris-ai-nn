"""First tester protocol CLI: all six commands; strict nonzero on blocker."""

from __future__ import annotations

from _first_tester_helpers import seed_rc

from solaris_ai_nn.cli import main


def test_first_tester_protocol_command(tmp_path):
    assert main(["first-tester-protocol", "--tester-state-dir",
                 str(tmp_path / "p")]) == 0


def test_first_tester_script_command(tmp_path):
    assert main(["first-tester-script", "--tester-state-dir",
                 str(tmp_path / "p")]) == 0


def test_first_tester_acceptance_command(tmp_path):
    assert main(["first-tester-acceptance", "--tester-state-dir",
                 str(tmp_path / "p")]) == 0


def test_first_tester_stops_command(tmp_path):
    assert main(["first-tester-stops", "--tester-state-dir",
                 str(tmp_path / "p")]) == 0


def test_first_tester_handoff_command(tmp_path):
    assert main(["first-tester-handoff", "--tester-state-dir",
                 str(tmp_path / "p")]) == 0


def test_first_tester_review_command(tmp_path):
    assert main(["first-tester-review", "--tester-state-dir",
                 str(tmp_path / "p")]) == 0


def test_strict_returns_nonzero_on_blocker(tmp_path):
    base = str(tmp_path / "blocked")
    seed_rc(base, "critical_blocked")
    rc = main(["first-tester-protocol", "--tester-state-dir", base, "--strict"])
    assert rc == 2


def test_strict_ready_returns_zero(tmp_path):
    base = str(tmp_path / "ready")
    seed_rc(base, "ready_with_warnings")
    assert main(["first-tester-protocol", "--tester-state-dir", base,
                 "--strict"]) == 0
