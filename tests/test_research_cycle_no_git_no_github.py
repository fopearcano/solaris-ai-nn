"""The cycle package runs no Git/GitHub/shell/subprocess; reports only."""

from __future__ import annotations

import inspect

from solaris_ai_nn import research_cycle


def test_no_subprocess_or_network_imports():
    import solaris_ai_nn.research_cycle.cycle_runtime as runtime
    import solaris_ai_nn.research_cycle.reports as reports
    for module in (runtime, reports):
        src = inspect.getsource(module)
        assert "subprocess" not in src
        assert "import requests" not in src
        assert "octokit" not in src
        assert "os.system" not in src


def test_status_flags_no_git_github_source():
    rt = research_cycle.ResearchCycleRuntime(state_dir="/tmp/rc_nogit_test")
    rt.load_bundle({"research_baseline": {"baseline_status": "validated"}})
    rt.run()
    st = rt.research_cycle_status()
    assert st["runs_git"] is False
    assert st["calls_github"] is False
    assert st["modifies_source"] is False


def test_safety_validator_blocks_git_github_ops():
    v = research_cycle.ResearchCycleSafetyValidator()
    assert not v.validate_operation("git push and open pull request").safe
    assert not v.validate_operation("call github api").safe
