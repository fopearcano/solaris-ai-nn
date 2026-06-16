"""Compiler: Inner MAP includes experiment-compiler state."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import ExperimentCompilerRuntime
from solaris_ai_nn.inner_map.observer import InnerMapObserver


def _runtime(tmp_path):
    rt = ExperimentCompilerRuntime(state_dir=str(tmp_path))
    rt.load_manifest(proposals=[{
        "proposal_id": "p1", "target": "revise_metabolism_thresholds",
        "proposal": "raise threshold", "evidence_refs": ["replication:ok"]}])
    rt.compile()
    return rt


def test_inner_map_includes_compiler(tmp_path):
    rt = _runtime(tmp_path)
    model = InnerMapObserver(experiment_compiler=rt).update()
    assert model.experiment_compiler is not None
    assert model.experiment_compiler["experiment_compiler_enabled"] is True
    assert model.experiment_compiler["modifies_source"] is False
    assert model.experiment_compiler["creates_branch"] is False
    assert "experiment_compiler" in model.to_dict()


def test_state_graph_has_compiler_nodes():
    from solaris_ai_nn.inner_map.state_graph import build_default_state_graph

    nodes = str(build_default_state_graph().to_dict())
    assert "ExperimentCompilerRuntime" in nodes
    assert "ImplementationPromptPack" in nodes
    assert "PRReadyBranchSpec" in nodes
