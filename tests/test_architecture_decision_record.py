"""ArchitectureDecisionRecord: serializes; operator review; MD/JSON written."""

from __future__ import annotations

import os

import pytest

from solaris_ai_nn.architecture_evolution import (
    ADRStore,
    ArchitectureDecisionRecord,
    DecisionType,
)


def test_adr_serializes():
    adr = ArchitectureDecisionRecord(title="prune latent",
                                     decision_type=DecisionType.PRUNE_MODULE,
                                     affected_modules=["latent"])
    d = adr.to_dict()
    assert d["decision_type"] == "prune_module"
    assert "no code change was applied" in d["note"]


def test_operator_review_required():
    adr = ArchitectureDecisionRecord(title="t",
                                     decision_type=DecisionType.KEEP_MODULE,
                                     operator_review_required=False)
    # The invariant forces operator review on regardless of the argument.
    assert adr.operator_review_required is True


def test_unknown_decision_type_rejected():
    with pytest.raises(ValueError):
        ArchitectureDecisionRecord(title="t", decision_type="rewrite_itself")


def test_markdown_and_json_generated(tmp_path):
    store = ADRStore(base_dir=str(tmp_path))
    adr = ArchitectureDecisionRecord(title="revise logos",
                                     decision_type=DecisionType.REVISE_MODULE,
                                     affected_modules=["logos_complexity"])
    paths = store.write(adr)
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])
    assert os.path.exists(os.path.join(str(tmp_path), "adr_index.jsonl"))
    assert store.snapshot()["adr_count"] == 1


def test_markdown_states_planning_only():
    adr = ArchitectureDecisionRecord(title="t",
                                     decision_type=DecisionType.PRUNE_MODULE)
    md = adr.render_markdown().lower()
    assert "does not modify code" in md
