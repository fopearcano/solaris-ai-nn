"""RC integration: live templates, console discovery, feedback guide, membrane docs."""

from __future__ import annotations

import os

from _tester_rc_helpers import run_rc, seed_ready_state

from solaris_ai_nn.tester_console.artifact_discovery import (
    ArtifactKind,
    ConsoleArtifactDiscovery,
)


def test_live_templates_included_in_bundle(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    rt = run_rc(base)
    included = {a["name"] for a in rt.bundle.manifest.included}
    # The external feeder policy (live README) is present in the repo examples.
    assert "EXTERNAL_FEEDER_POLICY.md" in included


def test_console_discovers_rc_artifacts(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    run_rc(base)
    disc = ConsoleArtifactDiscovery(
        tester_state_dir=base, state_dir=str(tmp_path / "live")).discover()
    assert disc.latest(ArtifactKind.TESTER_RC_MANIFEST) is not None
    assert disc.latest(ArtifactKind.TESTER_RC_RELEASE_NOTES) is not None
    assert disc.latest(ArtifactKind.TESTER_RC_RUNBOOK) is not None


def test_feedback_guide_included(tmp_path):
    base = str(tmp_path / "ready")
    seed_ready_state(base)
    rt = run_rc(base)
    assert os.path.isfile(rt.doc_paths["feedback_guide"])
    text = open(rt.doc_paths["feedback_guide"], encoding="utf-8").read().lower()
    assert "not training" in text


def test_membrane_docs_required_in_ctx(tmp_path):
    rt = run_rc(str(tmp_path / "rc"))
    mem = rt.ctx["membrane"]
    assert "module_available" in mem
    assert "integration_available" in mem
    # Sensory impression docs / bypass detection are tracked.
    assert mem["impression_docs"] is True
    assert mem["bypass_detection"] is True
