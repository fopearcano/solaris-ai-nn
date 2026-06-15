"""Architecture <-> Inner MAP: model field + state-graph nodes/edges."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_model_has_architecture_field():
    assert InnerMapModel().architecture_evolution is None


def test_observer_populates_architecture():
    observer = InnerMapObserver(architecture_evolution={
        "enabled": True,
        "inventory_count": 32,
        "open_adr_count": 2,
        "pruning_candidates": ["latent"],
        "modifies_source_code": False})
    model = observer.update()
    assert model.architecture_evolution is not None
    assert model.architecture_evolution["inventory_count"] == 32
    assert model.architecture_evolution["modifies_source_code"] is False


def test_state_graph_has_architecture_nodes():
    g = build_default_state_graph()
    for node in ("ModuleInventory", "ModuleLifecycleClassifier",
                 "ArchitectureDecisionRecord", "ArchitectureEvidenceMap",
                 "PruningProposalBuilder", "PromotionProposal",
                 "ImpactAnalyzer", "MigrationPlan", "DesignDebtRegistry",
                 "RoadmapCompiler", "ArchitectureSnapshotBuilder",
                 "ArchitectureReviewReportBuilder",
                 "ArchitectureEvolutionSafetyValidator"):
        assert node in g.nodes


def test_state_graph_architecture_edges():
    g = build_default_state_graph()
    pairs = {(s, d) for s, d, _ in g.edges}
    # Research evidence feeds the evidence map, which feeds the classifier.
    assert ("ResearchReportBuilder", "ArchitectureEvidenceMap") in pairs
    assert ("ArchitectureEvidenceMap", "ModuleLifecycleClassifier") in pairs
    # The classifier feeds the pruning proposal builder.
    assert ("ModuleLifecycleClassifier", "PruningProposalBuilder") in pairs
    # The review feeds Inner MAP (planning state, never a code change).
    assert ("ArchitectureReviewReportBuilder", "inner_map") in pairs
