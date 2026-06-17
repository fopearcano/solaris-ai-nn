"""Shared helpers for tester packaging tests (not a test module)."""

from __future__ import annotations

from solaris_ai_nn.tester_packaging import TesterPackagingRuntime


def run_packaging(tmp_path, **kwargs):
    rt = TesterPackagingRuntime(tester_state_dir=str(tmp_path), **kwargs)
    rt.run()
    return rt
