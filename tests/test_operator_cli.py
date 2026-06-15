"""Operator CLI: status/profiles/plan work; run needs confirm; approve guarded."""

from __future__ import annotations

from solaris_ai_nn.operator_console.cli import (
    EXIT_BLOCKED,
    EXIT_OK,
    main,
)


def _run(tmp_path, *args):
    return main(["--state-dir", str(tmp_path / "op"), *args])


def test_status_command_works(tmp_path, capsys):
    assert _run(tmp_path, "status") == EXIT_OK
    assert "available_profile_count" in capsys.readouterr().out


def test_profiles_command_works(tmp_path, capsys):
    assert _run(tmp_path, "profiles") == EXIT_OK
    assert "runnable" in capsys.readouterr().out


def test_plan_command_works(tmp_path, capsys):
    assert _run(tmp_path, "plan", "safety_fast_check") == EXIT_OK
    assert "external_authority" in capsys.readouterr().out


def test_run_without_confirm_blocked(tmp_path, capsys):
    assert _run(tmp_path, "run", "safety_fast_check") == EXIT_BLOCKED
    assert "confirm" in capsys.readouterr().out.lower()


def test_run_with_confirm_still_safe(tmp_path):
    # With --confirm but no safety state / orchestrator, the run is still
    # blocked safely (never silently executed).
    assert _run(tmp_path, "run", "safety_fast_check", "--confirm") \
        == EXIT_BLOCKED


def test_approve_forbidden_scope_blocked(tmp_path, capsys):
    rc = _run(tmp_path, "approve", "forbidden_real_world_actuation",
              "--note", "no")
    assert rc == EXIT_BLOCKED
    assert "blocked" in capsys.readouterr().out.lower()


def test_approve_allowed_scope_ok(tmp_path):
    assert _run(tmp_path, "approve", "bounded_fixture_run", "--note", "ok") \
        == EXIT_OK
