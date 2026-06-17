"""Live observation analyzers: window, source health, diet, rhythm, absence."""

from __future__ import annotations

from solaris_ai_nn.live_observation import (
    LiveAbsenceAnalyzer,
    LiveRhythmAnalyzer,
    LiveSourceDietAnalyzer,
    LiveSourceHealthEvaluator,
    ObservationWindowBuilder,
    SourceHealthStatus,
    parse_timestamp,
)

_SOURCES = ["chronos_absence", "machine_body", "operator_pulse"]


def _ev(eid, ts, sid, noise=0.0, absence=False, command=False, gloss_gt=False):
    return {"event_id": eid, "timestamp_utc": ts, "source_id": sid,
            "modality": "scalar", "channel": "c", "payload": {"v": 1},
            "is_command": command, "debug_gloss_is_ground_truth": gloss_gt,
            "human_label_is_ground_truth": False,
            "quality": {"completeness": 1.0, "noise": noise,
                        "is_absence": absence, "is_noisy": noise >= 0.5}}


def test_parse_timestamp_handles_z_and_naive():
    assert parse_timestamp("2026-06-17T08:00:00Z") is not None
    assert parse_timestamp("2026-06-17T08:00:00") is not None
    assert parse_timestamp("") is None
    assert parse_timestamp("not-a-time") is None


def test_window_empty_is_deprivation():
    w = ObservationWindowBuilder().build(
        window_id="w0", accepted_events=[], quarantined_count=0,
        expected_sources=_SOURCES).to_dict()
    assert w["status"] == "empty"
    assert "no_accepted_events" in w["deprivation_markers"]


def test_window_missing_expected_source_marked():
    events = [_ev("e1", "2026-06-17T08:00:00Z", "machine_body")]
    w = ObservationWindowBuilder().build(
        window_id="w1", accepted_events=events, quarantined_count=0,
        expected_sources=_SOURCES).to_dict()
    assert "chronos_absence" in w["missing_expected_sources"]
    assert "only_one_source_active" in w["deprivation_markers"]


def test_window_high_rate_overload():
    events = [_ev(f"e{i}", f"2026-06-17T08:00:{i * 0.1:06.3f}Z", "machine_body")
              for i in range(10)]
    w = ObservationWindowBuilder().build(
        window_id="w2", accepted_events=events, quarantined_count=0,
        expected_sources=["machine_body"]).to_dict()
    assert "peak_event_rate_too_high" in w["overload_markers"]


def test_source_health_silent_is_not_failure():
    healths = LiveSourceHealthEvaluator().evaluate(
        registered_sources=_SOURCES,
        accepted_events=[_ev("e1", "2026-06-17T08:00:00Z", "machine_body")],
        quarantine_by_source={})
    by_id = {h.source_id: h for h in healths}
    assert by_id["chronos_absence"].status == SourceHealthStatus.SILENT
    assert by_id["chronos_absence"].blocks_stability is False
    assert by_id["machine_body"].status in (
        SourceHealthStatus.HEALTHY, SourceHealthStatus.HEALTHY_WITH_WARNINGS)


def test_source_health_forbidden_blocks_stability():
    healths = LiveSourceHealthEvaluator().evaluate(
        registered_sources=["raw_microphone"],
        accepted_events=[_ev("e1", "2026-06-17T08:00:00Z", "raw_microphone")],
        quarantine_by_source={})
    summary = LiveSourceHealthEvaluator.summary(healths)
    assert summary["live_forbidden_source_count"] >= 1
    assert summary["blocks_stability"] is True


def test_source_diet_balanced_vs_operator_dominant():
    balanced = LiveSourceDietAnalyzer().analyze([
        _ev("a", "t", "chronos_absence"), _ev("b", "t", "machine_body"),
        _ev("c", "t", "operator_pulse"), _ev("d", "t", "project_artifact_field")])
    assert balanced.balance == "balanced"
    op = LiveSourceDietAnalyzer().analyze([
        _ev("a", "t", "operator_pulse"), _ev("b", "t", "operator_pulse"),
        _ev("c", "t", "machine_body")])
    assert op.balance == "operator_pulse_dominant"


def test_rhythm_periodic_detected_small_window_weak():
    events = [_ev(f"e{i}", f"2026-06-17T08:{i * 5:02d}:00Z", "machine_body")
              for i in range(6)]
    analysis = LiveRhythmAnalyzer().analyze(events).to_dict()
    assert analysis["periodic_source_count"] >= 1


def test_absence_global_silence_is_deprivation():
    a = LiveAbsenceAnalyzer().analyze(accepted_events=[],
                                      expected_sources=_SOURCES).to_dict()
    assert a["deprivation_window_count"] >= 1


def test_absence_explicit_is_stable_background():
    events = [_ev("e1", "2026-06-17T08:00:00Z", "chronos_absence", absence=True)]
    a = LiveAbsenceAnalyzer().analyze(
        accepted_events=events, expected_sources=["chronos_absence"]).to_dict()
    kinds = {w["kind"] for w in a["windows"]}
    assert "stable_background" in kinds
