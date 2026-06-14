"""Pilot-2 source curation: safe included, secret-like excluded with reason."""

from __future__ import annotations

from solaris_ai_nn.pilot2 import CuratedSourceSet
from solaris_ai_nn.sensory_membrane import SensorySourceConfig


def test_safe_source_included():
    cur = CuratedSourceSet()
    report = cur.curate([SensorySourceConfig(
        source_id="j", source_type="jsonl_file", path="/in/events.jsonl",
        enabled=True)])
    assert report.included
    assert report.included[0]["source_id"] == "j"


def test_secret_like_source_excluded():
    cur = CuratedSourceSet()
    report = cur.curate([SensorySourceConfig(
        source_id="sec", source_type="text_file",
        path="/in/secret_token.txt", enabled=True)])
    assert report.excluded
    assert "secret" in report.excluded[0]["reason"]


def test_excluded_reason_recorded():
    cur = CuratedSourceSet()
    report = cur.curate([SensorySourceConfig(
        source_id="net", source_type="jsonl_file", path="/in/e.jsonl",
        enabled=True, metadata={"network": True})])
    assert report.excluded
    assert "network" in report.excluded[0]["reason"]


def test_synthetic_preferred_first():
    cur = CuratedSourceSet()
    report = cur.curate([
        SensorySourceConfig(source_id="real", source_type="jsonl_file",
                            path="/in/e.jsonl", enabled=True),
        SensorySourceConfig(source_id="sim", source_type="manual_dump",
                            path="/in/dump.json", enabled=True)])
    # The simulated/manual source is sorted ahead of the real file source.
    assert report.included[0]["source_id"] == "sim"
