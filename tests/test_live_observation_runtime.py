"""Live observation runtime: bounded, gated, read-only, no learning, artifacts."""

from __future__ import annotations

import inspect
import json
import os

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import (
    PostBirthLiveObservationRuntime,
    available_profiles,
    default_observation_profile,
    get_observation_profile,
)


def _ev(eid, ts, sid, noise=0.0, absence=False, noisy=False):
    return {"event_id": eid, "timestamp_utc": ts, "source_id": sid,
            "modality": "scalar", "channel": "c", "read_only": True,
            "is_command": False, "human_label_is_ground_truth": False,
            "payload": {"v": 1},
            "quality": {"completeness": 1.0, "noise": noise,
                        "is_absence": absence, "is_noisy": noisy},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": False, "allow_learning": False}}


_BALANCED = [
    _ev("c1", "2026-06-17T08:00:00Z", "chronos_absence"),
    _ev("c2", "2026-06-17T08:10:00Z", "chronos_absence", absence=True),
    _ev("b1", "2026-06-17T08:02:00Z", "machine_body", noise=0.05),
    _ev("b2", "2026-06-17T08:12:00Z", "machine_body", noise=0.05),
    _ev("w1", "2026-06-17T08:05:00Z", "local_weather_readonly_external"),
    _ev("a1", "2026-06-17T08:07:00Z", "project_artifact_field"),
    _ev("e1", "2026-06-17T08:09:00Z", "local_environment_manual"),
    _ev("p1", "2026-06-17T08:15:00Z", "operator_pulse"),
]


def _setup(tmp_path, events=_BALANCED, cert=True):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    with open(os.path.join(state, "governance",
                           "LIVE_READONLY_GOVERNANCE.json"), "w") as fh:
        json.dump(approved_governance(), fh)
    with open(os.path.join(state, "feeders", "FEEDER_REGISTRY.json"), "w") as fh:
        json.dump(feeder_registry_template(), fh)
    if cert:
        with open(os.path.join(state, "certificates",
                               "BIRTH_CERTIFICATE_t.md"), "w") as fh:
            fh.write("# cert\n")
    with open(os.path.join(state, "inbox", "events.jsonl"), "w") as fh:
        for e in events:
            fh.write(json.dumps(e) + "\n")
    return state


def test_bounded_runtime_runs(tmp_path):
    state = _setup(tmp_path)
    rt = PostBirthLiveObservationRuntime(state_dir=state)
    assert rt.run()["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = PostBirthLiveObservationRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_balanced_field_ready_for_metabolism(tmp_path):
    state = _setup(tmp_path)
    rt = PostBirthLiveObservationRuntime(state_dir=state)
    res = rt.run()
    assert res["blocked"] is False
    assert res["accepted_event_count"] == 8
    assert res["live_stability_status"] == "ready_for_metabolism_calibration"


def test_missing_birth_certificate_blocks(tmp_path):
    state = _setup(tmp_path, cert=False)
    rt = PostBirthLiveObservationRuntime(state_dir=state,
                                         require_birth_certificate=True)
    res = rt.run()
    assert res["blocked"] is True
    assert any("birth certificate" in b for b in res["blockers"])


def test_status_flags_no_learning_no_control(tmp_path):
    state = _setup(tmp_path)
    rt = PostBirthLiveObservationRuntime(state_dir=state)
    rt.run()
    st = rt.observation_status()
    assert st["learns"] is False
    assert st["forms_concepts"] is False
    assert st["births_signs"] is False
    assert st["starts_feeders"] is False
    assert st["controls_hardware"] is False
    assert st["accesses_network"] is False
    assert st["runs_git"] is False


def test_artifacts_written(tmp_path):
    state = _setup(tmp_path)
    rt = PostBirthLiveObservationRuntime(state_dir=state)
    rt.run()
    reports = os.path.join(state, "observation", "reports")
    assert os.path.isfile(os.path.join(reports, "LIVE_OBSERVATION_REPORT.md"))
    first_day = os.path.join(state, "observation", "first_day")
    assert any(f.startswith("FIRST_DAY_RECORD_") for f in os.listdir(first_day))


def test_dry_run_writes_nothing(tmp_path):
    state = _setup(tmp_path)
    rt = PostBirthLiveObservationRuntime(state_dir=state, dry_run=True)
    rt.run()
    reports = os.path.join(state, "observation", "reports")
    assert not os.path.isdir(reports) or not os.listdir(reports)


def test_profiles_default_no_learning():
    p = default_observation_profile()
    assert p.learning_enabled is False
    assert p.governance_required is True
    assert "post_birth_observation_v0" in available_profiles()
    metab = get_observation_profile("first_day_metabolism_24h_v0")
    assert metab.is_metabolism_phase is True


def test_no_network_shell_git_in_source():
    import solaris_ai_nn.live_observation.observation_runtime as rt_mod

    src = inspect.getsource(rt_mod)
    assert "subprocess" not in src
    assert "urllib" not in src
    assert "os.system" not in src
