"""Console claims/docs/alpha integration: claim warnings, docs linked, alpha path."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _tester_console_helpers import build_console, stage_claim  # noqa: E402
from solaris_ai_nn.tester_console import ArtifactKind, SummaryCardKind  # noqa: E402


def test_claim_warnings_summarized(tmp_path):
    base = str(tmp_path)
    stage_claim(os.path.join(base, "claims"))
    rt = build_console(tmp_path, claims_dir=os.path.join(base, "claims"))
    claim = next(c for c in rt.cards if c.kind == SummaryCardKind.CLAIMS)
    assert claim.status == "blocker"
    assert claim.blockers


def test_docs_linked_if_present(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    # The repo docs (README/ARCHITECTURE) are discovered as architecture docs.
    assert rt.discovery.has(ArtifactKind.ARCHITECTURE_DOCS)


def test_alpha_exposes_console_path(tmp_path):
    rt = build_console(tmp_path, fixture=True)
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    status = AlphaResearchOrchestrator().tester_console_status(
        console_dir=rt.console_dir)
    assert status["console_available"] is True
    assert status["read_only"] is True
    assert status["runs_server"] is False


def test_alpha_absent_without_console(tmp_path):
    from solaris_ai_nn.alpha_system.alpha_orchestrator import (
        AlphaResearchOrchestrator)
    status = AlphaResearchOrchestrator().tester_console_status(
        console_dir=str(tmp_path / "none"))
    assert status["console_available"] is False
