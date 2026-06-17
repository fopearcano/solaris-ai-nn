"""Live ontogenesis runtime: bounded, reports, memory, no control, no learning."""

from __future__ import annotations

import inspect
import json
import os

from solaris_ai_nn.live_birth import approved_governance, feeder_registry_template
from solaris_ai_nn.live_observation import PostBirthLiveObservationRuntime
from solaris_ai_nn.live_ontogenesis import FirstLiveOntogenesisRuntime


def _ev(eid, ts, sid, modality, channel, payload, noise=0.0, absence=False):
    return {"event_id": eid, "timestamp_utc": ts, "source_id": sid,
            "modality": modality, "channel": channel, "read_only": True,
            "is_command": False, "human_label_is_ground_truth": False,
            "payload": payload,
            "quality": {"completeness": 1.0, "noise": noise,
                        "is_absence": absence, "is_noisy": noise >= 0.5},
            "safety": {"private_data": False, "contains_instruction": False,
                       "contains_secret": False, "allow_learning": False},
            "debug_gloss": "DEBUG ONLY", "debug_gloss_is_ground_truth": False}


def _events():
    rows = [_ev(f"b{i}", f"2026-06-18T08:0{i}:00Z", "machine_body", "scalar",
                "machine_body/load", {"load": 0.30 + i * 0.01}, noise=0.05)
            for i in range(6)]
    rows += [_ev(f"w{i}", f"2026-06-18T08:1{i}:00Z",
                 "local_weather_readonly_external", "scalar", "weather/temp",
                 {"temp_c": 19.0}) for i in range(4)]
    rows += [_ev(f"a{i}", f"2026-06-18T08:2{i}:00Z", "project_artifact_field",
                 "field", "artifact/counts", {"reports": 12}) for i in range(4)]
    rows += [_ev(f"ab{i}", f"2026-06-18T08:3{i}:00Z", "chronos_absence",
                 "chronos", "time/absence", {"absence": True}, absence=True)
             for i in range(3)]
    rows += [_ev("e0", "2026-06-18T08:40:00Z", "local_environment_manual",
                 "manual", "environment/x", {"v": 1}),
             _ev("op0", "2026-06-18T08:41:00Z", "operator_pulse", "pulse",
                 "operator/pulse", {"pulse": 1})]
    return rows


def _setup(tmp_path, run_observation=True):
    state = str(tmp_path)
    for sub in ("governance", "feeders", "inbox", "certificates"):
        os.makedirs(os.path.join(state, sub), exist_ok=True)
    json.dump(approved_governance(), open(os.path.join(
        state, "governance", "LIVE_READONLY_GOVERNANCE.json"), "w"))
    json.dump(feeder_registry_template(), open(os.path.join(
        state, "feeders", "FEEDER_REGISTRY.json"), "w"))
    open(os.path.join(state, "certificates", "BIRTH_CERTIFICATE_t.md"),
         "w").write("# cert\n")
    with open(os.path.join(state, "inbox", "ev.jsonl"), "w") as fh:
        for e in _events():
            fh.write(json.dumps(e) + "\n")
    if run_observation:
        PostBirthLiveObservationRuntime(state_dir=state).run()
    return state


def test_bounded_runtime_runs(tmp_path):
    state = _setup(tmp_path)
    rt = FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True)
    assert rt.run()["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = FirstLiveOntogenesisRuntime(state_dir=str(tmp_path), max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_reports_and_memory_generated(tmp_path):
    state = _setup(tmp_path)
    rt = FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True)
    rt.run()
    reports = os.path.join(state, "ontogenesis", "reports")
    assert os.path.isfile(os.path.join(reports, "LIVE_ONTOGENESIS_REPORT.md"))
    concepts = os.path.join(state, "ontogenesis", "concepts")
    assert os.path.isfile(os.path.join(concepts, "LIVE_CONCEPT_MEMORY.json"))


def test_status_flags_no_control_no_learning(tmp_path):
    state = _setup(tmp_path)
    rt = FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True)
    rt.run()
    st = rt.ontogenesis_status()
    assert st["enables_semiogenesis"] is False
    assert st["enables_action_reaction"] is False
    assert st["enables_developmental_autonomy"] is False
    assert st["starts_feeders"] is False
    assert st["controls_hardware"] is False
    assert st["accesses_network"] is False
    assert st["runs_git"] is False


def test_births_occur_on_stable_field(tmp_path):
    state = _setup(tmp_path)
    rt = FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=True)
    rt.run()
    assert rt.ontogenesis_status()["live_born_proto_concept_count"] >= 1


def test_candidate_only_default_withholds_birth(tmp_path):
    state = _setup(tmp_path)
    rt = FirstLiveOntogenesisRuntime(state_dir=state, allow_limited_birth=False)
    rt.run()
    assert rt.ontogenesis_status()["live_born_proto_concept_count"] == 0


def test_no_network_shell_git_in_source():
    import solaris_ai_nn.live_ontogenesis.ontogenesis_runtime as rt_mod

    src = inspect.getsource(rt_mod)
    assert "subprocess" not in src
    assert "urllib" not in src
    assert "os.system" not in src
