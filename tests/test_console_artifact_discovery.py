"""Console artifact discovery: discovers reports, warns on missing, no payloads."""

from __future__ import annotations

import os
import sys

from solaris_ai_nn.tester_console import ArtifactKind, ConsoleArtifactDiscovery

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import (  # noqa: E402
    stage_fixture,
    stage_membrane_bypass,
    write_json,
)


def test_discovers_fixture_report(tmp_path):
    tester = str(tmp_path / "tester")
    stage_fixture(tester)
    result = ConsoleArtifactDiscovery(
        state_dir=str(tmp_path / "live"), tester_state_dir=tester).discover()
    assert result.has(ArtifactKind.TESTER_FIXTURE_REPORT)


def test_discovers_membrane_report(tmp_path):
    live = str(tmp_path / "live")
    write_json(os.path.join(live, "membrane", "reports",
                            "ENVIRONMENTAL_MEMBRANE_REPORT.json"),
               {"membrane_impression_count": 5})
    result = ConsoleArtifactDiscovery(state_dir=live).discover()
    assert result.has(ArtifactKind.MEMBRANE_REPORT)
    art = result.latest(ArtifactKind.MEMBRANE_REPORT)
    assert art.summary.get("membrane_impression_count") == 5


def test_discovers_membrane_integration(tmp_path):
    live = str(tmp_path / "live")
    stage_membrane_bypass(live)
    result = ConsoleArtifactDiscovery(state_dir=live).discover()
    assert result.has(ArtifactKind.MEMBRANE_INTEGRATION_REPORT)


def test_missing_dirs_warn_not_crash(tmp_path):
    result = ConsoleArtifactDiscovery(
        state_dir=str(tmp_path / "nope_live"),
        tester_state_dir=str(tmp_path / "nope_tester")).discover()
    assert result.warnings
    assert result.artifacts == [] or all(
        a.state_root == "repo" for a in result.artifacts)


def test_private_payload_not_displayed(tmp_path):
    # Discovery summaries only surface safe scalar keys, never raw payloads.
    live = str(tmp_path / "live")
    write_json(os.path.join(live, "quarantine", "q.json"),
               {"quarantined_count": 1,
                "records": [{"payload": {"secret": "TOP_SECRET"}}]})
    result = ConsoleArtifactDiscovery(state_dir=live).discover()
    art = result.latest(ArtifactKind.QUARANTINE_REPORT)
    assert "records" not in art.summary
    assert "TOP_SECRET" not in str(art.summary)
