"""Console observation + optional layers: summarized; missing optional not failure."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import build_console, write_json  # noqa: E402
from solaris_ai_nn.tester_console import StageHealth, SummaryCardKind  # noqa: E402


def test_observation_report_summarized(tmp_path):
    live = os.path.join(str(tmp_path), "live")
    write_json(os.path.join(live, "observation", "reports",
                            "LIVE_OBSERVATION_REPORT.json"),
               {"live_observation_enabled": True})
    rt = build_console(tmp_path)
    obs = next(c for c in rt.cards if c.kind == SummaryCardKind.OBSERVATION)
    assert obs.status == "ok"


def test_optional_layers_summarized_if_present(tmp_path):
    live = os.path.join(str(tmp_path), "live")
    write_json(os.path.join(live, "ontogenesis", "concepts",
                            "LIVE_CONCEPT_MEMORY.json"), {"records": []})
    rt = build_console(tmp_path)
    st = rt.status.stage("live_ontogenesis")
    assert st.health == StageHealth.PASS


def test_missing_optional_not_failure(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    for stage_id in ("live_ontogenesis", "live_semiogenesis", "live_cognition"):
        st = rt.status.stage(stage_id)
        assert st.health == StageHealth.SKIPPED_OPTIONAL
        assert st.ok
