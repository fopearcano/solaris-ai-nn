"""Compiler consumes architecture-evolution proposals; falsified stays blocked."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import replication_revision_proposals
from solaris_ai_nn.experiment_compiler import ExperimentCompilerRuntime


def test_consumes_architecture_revision_proposals(tmp_path):
    # Architecture evolution produces proposal dicts; the compiler reads them.
    proposals = replication_revision_proposals({
        "replicated_claim_count": 4, "falsified_claim_count": 0,
        "diverged_claim_count": 0, "fixture_overfit_score": 0.8})
    assert proposals  # architecture evolution produced proposals
    for i, p in enumerate(proposals):
        p.setdefault("proposal_id", f"arch_{i}")
    rt = ExperimentCompilerRuntime(state_dir=str(tmp_path))
    rt.load_manifest(proposals=proposals)
    out = rt.compile()
    assert out["compiled"] >= 1


def test_consumes_experiment_queue_like_dicts(tmp_path):
    # An "experiment queue" is just a list of proposal dicts to the compiler.
    queue = [{"proposal_id": "q1", "target": "revise_sensorium_profiles",
              "proposal": "broaden diet"},
             {"proposal_id": "q2", "target": "revise_cognition_limits",
              "proposal": "raise limit"}]
    rt = ExperimentCompilerRuntime(state_dir=str(tmp_path))
    rt.load_manifest(proposals=queue)
    rt.compile()
    assert rt.compiler_status()["compiled_spec_count"] == 2


def test_blocked_falsified_proposal_remains_blocked(tmp_path):
    # A falsified architecture proposal (blocks_promotion) stays blocked.
    proposals = replication_revision_proposals({
        "falsified_claim_count": 2, "replicated_claim_count": 1})
    freeze = next(p for p in proposals
                  if p.get("target") == "freeze_unsupported_claims")
    freeze["proposal_id"] = "frozen"
    freeze["falsified"] = True
    rt = ExperimentCompilerRuntime(state_dir=str(tmp_path))
    rt.load_manifest(proposals=[freeze])
    rt.compile()
    assert rt.compiler_status()["blocked_spec_count"] == 1
    assert rt.blocked[0].spec.status == "blocked_by_falsification"
