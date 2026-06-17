"""Console fixture/live integration: fixture + live summarized, bundle paths shown."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import build_console, stage_fixture  # noqa: E402
from solaris_ai_nn.tester_console import SummaryCardKind  # noqa: E402


def test_fixture_report_summarized(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    fx = next(c for c in rt.cards if c.kind == SummaryCardKind.FIXTURE_DEMO)
    assert fx.report_path
    assert fx.status == "ok"


def test_live_report_summarized(tmp_path):
    # Run a real live tester (init only writes governance template, no live run).
    from solaris_ai_nn.tester_live_readonly import TesterLiveReadOnlyRuntime
    tester = str(tmp_path / "tester")
    TesterLiveReadOnlyRuntime(
        state_dir=str(tmp_path / "live"),
        tester_state_dir=os.path.join(tester, "live"),
        profile="tester_live_init_only_v0").run()
    rt = build_console(tmp_path)
    live = next(c for c in rt.cards if c.kind == SummaryCardKind.LIVE_TESTER)
    assert live is not None


def test_bundle_paths_shown(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    bundle = next(c for c in rt.cards
                  if c.kind == SummaryCardKind.ARTIFACT_BUNDLE)
    assert bundle.report_path  # the fixture bundle manifest path
