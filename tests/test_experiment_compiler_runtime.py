"""Compiler runtime: bounded, documents only, no source/branch/PR/agent."""

from __future__ import annotations

import inspect

from solaris_ai_nn.experiment_compiler import ExperimentCompilerRuntime
from solaris_ai_nn.experiment_compiler import compiler_runtime


def _proposals():
    return [
        {"proposal_id": "p1", "target": "revise_sensorium_profiles",
         "proposal": "broaden diet", "evidence_refs": ["replication:overfit"]},
        {"proposal_id": "p2", "target": "actuate robot", "safe": False}]


def test_bounded_runtime(tmp_path):
    rt = ExperimentCompilerRuntime(state_dir=str(tmp_path), max_specs=10)
    rt.load_manifest(proposals=_proposals())
    out = rt.compile()
    assert out["refused"] is False
    assert out["compiled"] == 1 and out["blocked"] == 1


def test_unbounded_refused(tmp_path):
    rt = ExperimentCompilerRuntime(state_dir=str(tmp_path), max_specs=0,
                                   max_prompt_packs=0)
    rt.load_manifest(proposals=_proposals())
    assert rt.compile()["refused"] is True


def test_documents_generated(tmp_path):
    rt = ExperimentCompilerRuntime(state_dir=str(tmp_path))
    rt.load_manifest(proposals=_proposals())
    rt.compile()
    out = rt.write_artifacts()
    import os
    assert os.path.isfile(out["markdown"])
    assert os.path.isfile(out["index"])
    assert out["per_experiment"]


def test_status_disclaims_mutation(tmp_path):
    rt = ExperimentCompilerRuntime(state_dir=str(tmp_path))
    rt.load_manifest(proposals=_proposals())
    rt.compile()
    st = rt.compiler_status()
    assert st["modifies_source"] is False
    assert st["creates_branch"] is False
    assert st["opens_pr"] is False
    assert st["runs_external_agent"] is False


def test_no_source_branch_pr_agent_in_source():
    src = inspect.getsource(compiler_runtime)
    assert "subprocess" not in src
    assert "git checkout" not in src
    assert "gh pr" not in src
    assert "open(" not in src or "os.system" not in src
