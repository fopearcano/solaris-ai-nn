"""Sensory impression: serializes, evidence required, gloss not truth, pulse not teaching."""

from __future__ import annotations

import os

from solaris_ai_nn.environmental_membrane import (
    SensoryImpression,
    SensoryImpressionGrounding,
    SensoryImpressionKind,
    SensoryImpressionStore,
)


def _impression():
    return SensoryImpression(
        impression_id="imp1", source_event_id="e1",
        timestamp_utc="2026-06-20T08:00:00Z", source_id="machine_body",
        receptor_id="machine_body_receptor", modality="scalar",
        channel="machine_body/load",
        impression_kind=SensoryImpressionKind.MACHINE_BODY_PRESSURE,
        grounding=SensoryImpressionGrounding.PRESSURE_BASED,
        evidence_refs=["e1"], debug_gloss_annotation="DEBUG ONLY: hint",
        operator_pulse_weight=0.0)


def test_impression_serializes():
    d = _impression().to_dict()
    assert d["impression_id"] == "imp1"
    assert d["impression_kind"] == "machine_body_pressure"
    assert d["grounding"] == "pressure_based"


def test_evidence_refs_required():
    d = _impression().to_dict()
    assert d["evidence_refs"] == ["e1"]
    assert d["source_event_id"] == "e1"


def test_debug_gloss_not_grounding_truth():
    d = _impression().to_dict()
    assert d["debug_gloss_is_ground_truth"] is False
    assert d["debug_gloss_annotation"]  # preserved as annotation only


def test_operator_pulse_not_teaching():
    imp = _impression()
    imp.operator_pulse_weight = 1.0
    assert imp.to_dict()["operator_pulse_is_teaching"] is False


def test_store_writes_index(tmp_path):
    store = SensoryImpressionStore(state_dir=str(tmp_path))
    store.add(_impression())
    paths = store.write()
    assert os.path.isfile(paths["jsonl"])
    assert os.path.isfile(paths["index_json"])
    idx = store.index()
    assert idx["membrane_impression_count"] == 1
