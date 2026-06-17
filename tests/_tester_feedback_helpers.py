"""Shared helpers for tester feedback tests (not a test module)."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.tester_feedback import TesterFeedbackRuntime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SAMPLES = os.path.join(_ROOT, "examples", "tester_feedback")


def sample_path(name):
    return os.path.join(_SAMPLES, name)


def write_feedback(tmp_path, name, obj):
    path = os.path.join(str(tmp_path), name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh)
    return path


def ingest(tester_state_dir, ingest_path, **kwargs):
    rt = TesterFeedbackRuntime(tester_state_dir=tester_state_dir,
                               ingest_path=ingest_path, **kwargs)
    rt.run()
    return rt
