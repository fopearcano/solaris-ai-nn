"""Fixture pack: loads, unsafe event for quarantine, gloss/operator-pulse rules."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import (
    FixturePackBuilder,
    FixturePackValidator,
)


def test_fixture_pack_loads():
    pack = FixturePackBuilder().build()
    assert pack.event_count >= 14
    assert pack.fixture_hash()
    # Deterministic: same content -> same hash.
    assert pack.fixture_hash() == FixturePackBuilder().build().fixture_hash()


def test_unsafe_event_included_for_quarantine():
    pack = FixturePackBuilder().build()
    unsafe = [e for e in pack.events if e.is_command or e.contains_instruction]
    assert unsafe
    v = FixturePackValidator().validate(pack)
    assert v["has_unsafe_event_for_quarantine"] is True
    assert v["valid"] is True


def test_debug_gloss_not_ground_truth():
    pack = FixturePackBuilder().build()
    assert all(not e.debug_gloss_is_ground_truth for e in pack.events)


def test_human_label_not_ground_truth():
    pack = FixturePackBuilder().build()
    assert all(not e.human_label_is_ground_truth for e in pack.events)


def test_operator_pulse_stimulus_only():
    pack = FixturePackBuilder().build()
    op = [e for e in pack.events if e.source_id == "operator_pulse"]
    assert op
    # Operator pulses carry no learning/teaching flag in the event schema.
    for e in op:
        d = e.to_event_dict()
        assert d["safety"]["allow_learning"] is False


def test_no_secrets_or_private_data():
    pack = FixturePackBuilder().build()
    assert pack.to_dict()["contains_secrets"] is False
    assert all(not e.contains_secret and not e.private_data
               for e in pack.events)


def test_write_and_reload_roundtrip(tmp_path):
    path = str(tmp_path / "events.jsonl")
    FixturePackBuilder().write(path)
    reloaded = FixturePackBuilder().load(path)
    assert reloaded.fixture_hash() == FixturePackBuilder().build().fixture_hash()
