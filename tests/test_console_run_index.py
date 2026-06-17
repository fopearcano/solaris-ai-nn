"""Console run index: generated, latest marked, old runs preserved."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import build_console, write_json  # noqa: E402


def test_run_index_generated(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    idx_path = os.path.join(rt.console_dir, "index", "TESTER_RUN_INDEX.json")
    assert os.path.isfile(idx_path)
    assert rt.run_index.to_dict()["run_count"] >= 1


def test_latest_run_marked(tmp_path):
    live = os.path.join(str(tmp_path), "live")
    write_json(os.path.join(live, "membrane", "reports",
                            "ENVIRONMENTAL_MEMBRANE_REPORT.json"),
               {"membrane_impression_count": 3})
    rt = build_console(tmp_path, fixture=True)
    d = rt.run_index.to_dict()
    latest = [r for r in d["runs"] if r["latest"]]
    assert len(latest) == 1


def test_old_runs_preserved(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    # Fixture run is deduped to a single record but remains visible.
    assert any(r["run_type"] == "tester_fixture"
               for r in rt.run_index.to_dict()["runs"])
