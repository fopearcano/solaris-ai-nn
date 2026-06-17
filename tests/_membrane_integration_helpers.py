"""Shared helpers for membrane integration tests (not a test module)."""

from __future__ import annotations

import json
import os
import shutil

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FIX = os.path.join(_ROOT, "examples", "membrane_integration",
                    "sample_membrane_pipeline")


def stage_pipeline(state_dir, *, include_bypass=False, contaminated=False):
    """Stage membrane impressions + downstream memories into a state dir."""
    def _w(rel, src):
        path = os.path.join(state_dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.copy(os.path.join(_FIX, src), path)

    imp_src = ("sensory_impressions.jsonl" if not contaminated
               else "sensory_impressions.jsonl")
    _w("membrane/impressions/SENSORY_IMPRESSIONS.jsonl", imp_src)
    os.makedirs(os.path.join(state_dir, "membrane", "reports"), exist_ok=True)
    with open(os.path.join(state_dir, "membrane", "reports",
                           "ENVIRONMENTAL_MEMBRANE_REPORT.json"), "w") as fh:
        json.dump({"sections": {}}, fh)
    concept = "bypass_concept.json" if include_bypass else "proto_concept.json"
    _w("ontogenesis/concepts/LIVE_CONCEPT_MEMORY.json", concept)
    _w("semiogenesis/signs/LIVE_SIGN_MEMORY.json", "sign_record.json")
    _w("cognition/traces/LIVE_COGNITION_MEMORY.json", "cognition_trace.json")
    return state_dir


def load_fixture(name):
    return json.load(open(os.path.join(_FIX, name)))
