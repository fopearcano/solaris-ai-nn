"""Pilot-1 retention policy: protect evidence, allow temp deletion, archive."""

from __future__ import annotations

from solaris_ai_nn.pilot1 import RetentionCategory, RetentionPolicy


def test_safety_incidents_retained():
    pol = RetentionPolicy()
    d = pol.classify("incidents.jsonl")
    assert d.protected is True
    assert not pol.can_delete(d)


def test_emergency_and_identity_retained():
    pol = RetentionPolicy()
    assert pol.classify("EMERGENCY_STOP").protected
    assert pol.classify("identity_anchor.json").protected
    assert pol.classify("restart_meta.json").protected


def test_fossil_fossilized():
    pol = RetentionPolicy()
    d = pol.classify("fossil_memory.json")
    assert d.category == RetentionCategory.FOSSILIZE
    assert d.protected


def test_temp_files_deletable():
    pol = RetentionPolicy()
    d = pol.classify("scratch_tmp_001.tmp")
    assert d.deletable
    assert pol.can_delete(d) is True


def test_evidence_requires_archive():
    pol = RetentionPolicy()
    # An aged, non-temp, non-protected artifact needs an archive before delete.
    d = pol.classify("telemetry_old.jsonl", age_days=120)
    assert d.requires_archive
    assert pol.can_delete(d, archived=False) is False
    assert pol.can_delete(d, archived=True) is True


def test_autoregeneration_context():
    pol = RetentionPolicy()
    pol.classify("warm.jsonl", age_days=10)
    ctx = pol.autoregeneration_context()
    assert "compress" in ctx and "delete_temp" in ctx
