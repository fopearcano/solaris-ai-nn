"""Shared helpers for tester safety freeze tests (not a test module)."""

from __future__ import annotations

import os

from solaris_ai_nn.tester_safety_freeze import TesterSafetyFreezeRuntime


def write(tmp_path, name, text):
    path = os.path.join(str(tmp_path), name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def run_freeze(tmp_path, **kwargs):
    rt = TesterSafetyFreezeRuntime(tester_state_dir=str(tmp_path), **kwargs)
    rt.run()
    return rt
