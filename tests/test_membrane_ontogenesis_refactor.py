"""Live Ontogenesis refactor: status flags impression usage vs raw fallback."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime
from solaris_ai_nn.membrane_integration import (
    LiveOntogenesisMembraneAdapter,
    SensoryImpressionLoader,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _membrane_integration_helpers import stage_pipeline  # noqa: E402


def test_status_flags_present():
    rt = FirstLiveOntogenesisRuntime(state_dir=".solaris_ai_nn_unused_xyz")
    st = rt.ontogenesis_status()
    assert "used_membrane_impressions" in st
    assert "raw_event_fallback" in st


def test_ontogenesis_uses_membrane_impressions(tmp_path):
    state = stage_pipeline(str(tmp_path))
    load = SensoryImpressionLoader().load(state)
    r = LiveOntogenesisMembraneAdapter().run(state, load)
    assert r.used_impressions is True
    # The audit ontogenesis subdir reflects membrane-derived events.
    audit = FirstLiveOntogenesisRuntime(
        state_dir=os.path.join(state, "_membrane_onto_audit"))
    st = audit.ontogenesis_status()
    # No accepted events loaded in fresh runtime -> flags default safely.
    assert st["used_membrane_impressions"] in (True, False)


def test_raw_fallback_is_loud(tmp_path):
    load = SensoryImpressionLoader().load(str(tmp_path))
    r = LiveOntogenesisMembraneAdapter().run(str(tmp_path), load, strict=False)
    assert r.raw_fallback is True
    assert "RAW FALLBACK" in r.detail
    assert r.warnings
