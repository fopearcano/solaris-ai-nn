"""Developmental lineage: relations, no ancestry language, checkpoint branch."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import (
    DevelopmentalLineage,
    LineageNode,
    LineageRelation,
)


def test_lineage_relation_created():
    lin = DevelopmentalLineage(lineage_id="L1")
    lin.add_node(LineageNode(run_id="a"))
    lin.add_node(LineageNode(run_id="b"))
    edge = lin.relate("a", "b", LineageRelation.DIFFERENT_SEED)
    assert edge["relation"] == LineageRelation.DIFFERENT_SEED
    assert edge["biological_ancestry"] is False


def test_unknown_relation_falls_back():
    lin = DevelopmentalLineage()
    edge = lin.relate("a", "b", "not_a_relation")
    assert edge["relation"] == LineageRelation.UNKNOWN_RELATION


def test_no_biological_ancestry_language():
    lin = DevelopmentalLineage()
    note = lin.to_dict()["note"]
    assert "not biological ancestry" in note
    for edge in lin.edges:
        assert edge["biological_ancestry"] is False


def test_checkpoint_branch_metadata_works():
    lin = DevelopmentalLineage()
    edge = lin.branch_from_checkpoint("a", "b", checkpoint_id="cp_3")
    assert edge["relation"] == LineageRelation.BRANCH_FROM_CHECKPOINT
    assert "cp_3" in edge["detail"]
    assert "metadata only" in edge["detail"]


def test_compare_records_differences():
    lin = DevelopmentalLineage()
    parent = {"run_id": "a", "sensorium_profile": "non_human",
              "source_diet": {"rf": 10},
              "developmental_profile": {"structural_growth_status":
                                        "real_structural_growth"}}
    child = {"run_id": "b", "sensorium_profile": "human_like",
             "source_diet": {"txt": 10},
             "developmental_profile": {"structural_growth_status":
                                       "fixture_overfit"}}
    comp = lin.compare(parent, child)
    assert comp.sensorium_differences
    assert comp.developmental_differences
    assert "not biological ancestry" in comp.to_dict()["limitations"][0]
