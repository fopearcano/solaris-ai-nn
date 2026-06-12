"""Tests for the proto-language report builder."""

from __future__ import annotations

import json

from solaris_ai_nn.governance.compliance import ClaimGuard
from solaris_ai_nn.protolanguage.layer import ProtoLanguageLayer
from solaris_ai_nn.protolanguage.reports import (
    PROTO_LANGUAGE_LIMITATIONS,
    ProtoLanguageReportBuilder,
)


def _layer(tmp_path):
    layer = ProtoLanguageLayer(state_dir=tmp_path)
    layer.process_context({
        "repeated_stimulus_patterns": {"light_noise": 5},
        "absence_states": {"silence": 4},
        "mysterium_spikes": {"prediction_miss": 3},
        "symbol_stream": ["ABS_0001", "NEED_0001", "ACT_0001"]})
    tokens = [s.token for s in list(layer.registry.symbols.values())[:2]]
    layer.utterances.build(tokens, purpose="report_support")
    return layer


def test_json_report_generated(tmp_path):
    builder = ProtoLanguageReportBuilder(_layer(tmp_path))
    data = json.loads(builder.to_json())
    for section in ("symbol_count_by_type", "newest_symbols",
                    "strongest_symbols", "ambiguous_symbols",
                    "extinct_or_decayed_symbols",
                    "repeated_symbol_sequences",
                    "proto_syntactic_regularities",
                    "compression_utility", "prediction_utility",
                    "grounding_stability",
                    "mysterium_related_symbols",
                    "milestones_as_symbols",
                    "example_proto_utterances"):
        assert section in data["sections"], section


def test_markdown_report_generated(tmp_path):
    md = ProtoLanguageReportBuilder(_layer(tmp_path)).to_markdown()
    assert md.startswith("# Proto-language report")
    assert "Strongest Symbols" in md
    assert "Proto Syntactic Regularities" in md


def test_limitations_included(tmp_path):
    md = ProtoLanguageReportBuilder(_layer(tmp_path)).to_markdown()
    for limitation in PROTO_LANGUAGE_LIMITATIONS:
        assert limitation[:50] in md
    assert "not human language" in md.lower()
    assert "no consciousness claim" in md.lower()


def test_claim_guard_scans_report(tmp_path):
    layer = _layer(tmp_path)
    builder = ProtoLanguageReportBuilder(layer)
    paths = builder.save(tmp_path / "pl.json", tmp_path / "pl.md")
    assert paths["claim_guard"]["safe"] is True
    assert ClaimGuard().is_safe((tmp_path / "pl.md").read_text())
    assert layer.report_path == str(tmp_path / "pl.md")
    assert layer.summary()["proto_language_report_path"] \
        == str(tmp_path / "pl.md")
