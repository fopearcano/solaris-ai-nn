"""Post-pilot research dossier: Markdown + JSON, no marketing/consciousness."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.post_pilot import (
    PilotArtifactLoader,
    ResearchDossierBuilder,
)


def _arts(tmp_path):
    base = tmp_path / "pilot1"
    state = tmp_path / "state"
    base.mkdir()
    state.mkdir()
    (base / "observability.jsonl").write_text(
        json.dumps({"kind": "metrics", "payload": {}}) + "\n")
    (state / "developmental_state.json").write_text(
        json.dumps({"epoch": "infancy"}))
    return PilotArtifactLoader(str(base), str(state)).load(), str(base)


def test_markdown_and_json_generated(tmp_path):
    arts, base = _arts(tmp_path)
    dossier = ResearchDossierBuilder(base_dir=base).build_and_write(
        artifacts=arts)
    paths = dossier.sections["dossier_paths"]
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])


def test_no_consciousness_or_marketing_claims(tmp_path):
    arts, base = _arts(tmp_path)
    dossier = ResearchDossierBuilder(base_dir=base).build(artifacts=arts)
    text = dossier.narrative.lower()
    for banned in ("is conscious", "is alive", "revolutionary", "breakthrough",
                   "sentient being"):
        assert banned not in text
    assert "no claim of consciousness" in text or "not" in text


def test_limitations_included(tmp_path):
    arts, base = _arts(tmp_path)
    dossier = ResearchDossierBuilder(base_dir=base).build(artifacts=arts)
    assert "## Limitations" in dossier.narrative
    assert dossier.sections["limitations"]


def test_claim_guard_safe(tmp_path):
    arts, base = _arts(tmp_path)
    dossier = ResearchDossierBuilder(base_dir=base).build(artifacts=arts)
    assert dossier.claim_guard_safe is True
