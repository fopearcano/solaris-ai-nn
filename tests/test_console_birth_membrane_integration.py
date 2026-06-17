"""Console birth/membrane integration: birth + membrane + bypass summarized."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import (  # noqa: E402
    build_console,
    stage_membrane_bypass,
    write_json,
)
from solaris_ai_nn.tester_console import SummaryCardKind  # noqa: E402


def test_birth_report_summarized(tmp_path):
    live = os.path.join(str(tmp_path), "live")
    write_json(os.path.join(live, "reports", "LIVE_BIRTH_REPORT.json"),
               {"live_birth_enabled": True, "accepted_event_count": 5,
                "quarantined_event_count": 1})
    rt = build_console(tmp_path)
    st = rt.status.stage("live_birth")
    assert st.health in ("pass", "blocked")


def test_membrane_report_summarized(tmp_path):
    live = os.path.join(str(tmp_path), "live")
    write_json(os.path.join(live, "membrane", "reports",
                            "ENVIRONMENTAL_MEMBRANE_REPORT.json"),
               {"membrane_impression_count": 6,
                "source_pressure_status": "balanced"})
    rt = build_console(tmp_path)
    mem = next(c for c in rt.cards if c.kind == SummaryCardKind.MEMBRANE)
    assert mem.status == "ok"


def test_membrane_integration_bypass_summarized(tmp_path):
    stage_membrane_bypass(os.path.join(str(tmp_path), "live"))
    rt = build_console(tmp_path)
    integ = next(c for c in rt.cards
                 if c.kind == SummaryCardKind.MEMBRANE_INTEGRATION)
    assert integ.metrics.get("critical_bypass_count") == 2
    assert integ.status == "blocker"
