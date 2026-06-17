"""Live feature extraction: scalar/absence features; gloss/pulse never truth."""

from __future__ import annotations

from solaris_ai_nn.live_ontogenesis import LiveFeatureExtractor


def _ev(eid, sid, payload, modality="scalar", channel="c", absence=False,
        gloss_gt=False, secret=False):
    return {"event_id": eid, "timestamp_utc": "2026-06-18T08:00:00Z",
            "source_id": sid, "modality": modality, "channel": channel,
            "is_command": False, "human_label_is_ground_truth": False,
            "payload": payload,
            "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": absence,
                        "is_noisy": False},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": secret, "allow_learning": False},
            "debug_gloss": "DEBUG ONLY: annotation", "debug_gloss_is_ground_truth": gloss_gt}


def test_scalar_features_extracted():
    res = LiveFeatureExtractor().extract(accepted_events=[
        _ev("e1", "machine_body", {"load": 0.3})])
    assert res.feature_vector_count == 1
    assert res.vectors[0].scalar_values.get("load")


def test_absence_features_extracted():
    res = LiveFeatureExtractor().extract(accepted_events=[
        _ev("e1", "chronos_absence", {"absence": True}, modality="chronos",
            absence=True)])
    assert res.vectors[0].is_absence is True


def test_debug_gloss_not_ground_truth():
    res = LiveFeatureExtractor().extract(accepted_events=[
        _ev("e1", "machine_body", {"load": 0.3}, gloss_gt=True)])
    d = res.vectors[0].to_dict()
    assert d["debug_gloss_is_ground_truth"] is False
    assert d["human_label_is_ground_truth"] is False
    # The *attempt* is recorded so contamination can reject it.
    assert d["attempted_debug_gloss_ground_truth"] is True
    assert d["debug_gloss_annotation"]  # kept as annotation


def test_operator_pulse_marked_not_teaching():
    res = LiveFeatureExtractor().extract(accepted_events=[
        _ev("e1", "operator_pulse", {"pulse": 1}, modality="pulse")])
    v = res.vectors[0]
    assert v.is_operator_pulse is True
    assert v.is_human_text_source is True


def test_secret_event_never_extracted():
    res = LiveFeatureExtractor().extract(accepted_events=[
        _ev("e1", "machine_body", {"load": 0.3}, secret=True)])
    assert res.feature_vector_count == 0
    assert res.skipped_count == 1
