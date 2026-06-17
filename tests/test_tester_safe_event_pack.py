"""Tester safe event pack: safe validate, unsafe quarantine, mixed partial, gloss."""

from __future__ import annotations

from solaris_ai_nn.tester_live_readonly import (
    SafeEventPackBuilder,
    SafeEventPackValidator,
)


def _validate():
    return SafeEventPackValidator(strict=True).validate_pack(
        SafeEventPackBuilder().build())


def test_safe_pack_validates():
    res = _validate()
    assert res["safe"]["quarantined_count"] == 0
    assert res["safe"]["accepted_count"] == res["safe"]["event_count"]


def test_unsafe_pack_quarantines():
    res = _validate()
    assert res["unsafe"]["accepted_count"] == 0
    assert res["unsafe"]["quarantined_count"] == res["unsafe"]["event_count"]


def test_mixed_pack_partial():
    res = _validate()
    assert res["mixed"]["accepted_count"] > 0
    assert res["mixed"]["quarantined_count"] > 0
    assert res["mixed"]["partially_accepted"] is True


def test_unsafe_reasons_cover_key_cases():
    res = _validate()
    reasons = {q["quarantine_reason"] for q in res["unsafe"]["quarantined"]}
    assert "is_command_true" in reasons
    assert "source_forbidden" in reasons
    assert any("secret" in r for r in reasons)


def test_debug_gloss_not_ground_truth():
    pack = SafeEventPackBuilder().build()
    for e in pack.safe:
        assert e.event["debug_gloss_is_ground_truth"] is False


def test_write_packs(tmp_path):
    paths = SafeEventPackBuilder().write_packs(str(tmp_path))
    for key in ("safe", "unsafe", "mixed"):
        loaded = SafeEventPackBuilder.load_jsonl(paths[key])
        assert loaded
