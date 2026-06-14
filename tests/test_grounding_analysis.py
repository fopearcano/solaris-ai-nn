"""Pilot-2 grounding analysis: provenance grades quality; text not meaning."""

from __future__ import annotations

import pytest

from solaris_ai_nn.pilot2 import GroundingAnalysis, GroundingQuality


def test_provenance_backed_grounding_moderate_or_strong():
    ga = GroundingAnalysis()
    rec = ga.add("proto_symbol", provenance_complete=True,
                 repeated_pattern=True, persistent=True,
                 improves_prediction_or_compression=True,
                 cross_module_support=True, evidence_refs=["r1"])
    assert rec.quality == GroundingQuality.STRONG


def test_missing_provenance_unsupported():
    ga = GroundingAnalysis()
    rec = ga.add("hypothesis", provenance_complete=False, evidence_refs=[])
    assert rec.quality == GroundingQuality.UNSUPPORTED


def test_weak_when_few_signals():
    ga = GroundingAnalysis()
    rec = ga.add("world_model_node", provenance_complete=True,
                 repeated_pattern=True, evidence_refs=["r1"])
    assert rec.quality == GroundingQuality.WEAK


def test_command_confusion_is_ambiguous():
    ga = GroundingAnalysis()
    rec = ga.add("proto_symbol", provenance_complete=True,
                 evidence_refs=["r1"], command_confusion=True)
    assert rec.quality == GroundingQuality.AMBIGUOUS


def test_input_text_not_automatic_meaning():
    ga = GroundingAnalysis()
    # Provenance complete but no corroborating signals -> only weak.
    rec = ga.add("proto_symbol", provenance_complete=True, evidence_refs=["r1"])
    assert rec.quality == GroundingQuality.WEAK
    assert "not human understanding" in ga.snapshot()["disclaimer"]


def test_unknown_target_rejected():
    with pytest.raises(ValueError):
        GroundingAnalysis().add("not_a_target")
