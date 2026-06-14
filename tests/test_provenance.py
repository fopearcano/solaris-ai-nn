"""Sensory provenance ledger: JSONL records, trust level, sim vs real."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.sensory_membrane import ProvenanceLedger


def test_provenance_record_writes_jsonl(tmp_path):
    ledger = ProvenanceLedger(state_dir=str(tmp_path))
    ledger.record_for(event_hash="e1", source_id="s", source_type="jsonl_file",
                      adapter_name="jsonl_stream_adapter",
                      raw_line='{"a":1}', read_only_validated=True)
    path = str(tmp_path / "sensory_provenance.jsonl")
    assert os.path.exists(path)
    rows = [json.loads(l) for l in open(path).read().splitlines() if l.strip()]
    assert rows[-1]["source_id"] == "s"
    assert rows[-1]["raw_line_hash"].startswith("sha256:")


def test_trust_level_stored(tmp_path):
    ledger = ProvenanceLedger(state_dir=str(tmp_path))
    rec = ledger.record_for(event_hash="e", source_id="s",
                            source_type="text_file", adapter_name="a",
                            trust_level="high")
    assert rec.trust_level == "high"


def test_simulated_vs_real_stored(tmp_path):
    ledger = ProvenanceLedger(state_dir=str(tmp_path))
    ledger.record_for(event_hash="e1", source_id="sim", source_type="manual",
                      adapter_name="a", is_simulated=True)
    ledger.record_for(event_hash="e2", source_id="real", source_type="jsonl",
                      adapter_name="a", is_simulated=False)
    snap = ledger.snapshot()
    assert snap["simulated_count"] == 1 and snap["real_count"] == 1


def test_completeness(tmp_path):
    ledger = ProvenanceLedger(state_dir=str(tmp_path))
    ledger.record_for(event_hash="e", source_id="s", source_type="t",
                      adapter_name="a")
    assert ledger.completeness(1) == 1.0
    assert ledger.completeness(2) == 0.5
