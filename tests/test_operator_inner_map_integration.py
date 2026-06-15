"""Operator <-> Inner MAP: model field + state-graph nodes/edges."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_model_has_operator_console_field():
    assert InnerMapModel().operator_console is None


def test_observer_populates_operator_console():
    observer = InnerMapObserver(operator_console={
        "operator_console_enabled": True,
        "available_profile_count": 60, "blocked_profile_count": 3,
        "latest_status_board_path": "/x/STATUS_BOARD.md",
        "real_world_authority": False})
    model = observer.update()
    assert model.operator_console is not None
    assert model.operator_console["available_profile_count"] == 60
    assert model.operator_console["real_world_authority"] is False


def test_state_graph_has_operator_nodes():
    g = build_default_state_graph()
    for node in ("OperatorConsoleConfig", "ProfileCatalog", "RunPlanner",
                 "RunLauncher", "ApprovalLedger", "EvidenceNavigator",
                 "ArtifactIndex", "ReportIndex", "OperatorStatusBoard",
                 "OperatorDecisionBoard", "NextActionRecommender",
                 "ExportBundleBuilder", "OperatorSessionLog",
                 "OperatorConsoleSafetyValidator"):
        assert node in g.nodes


def test_state_graph_operator_edges():
    g = build_default_state_graph()
    pairs = {(s, d) for s, d, _ in g.edges}
    assert ("ProfileCatalog", "RunPlanner") in pairs
    assert ("RunPlanner", "RunLauncher") in pairs
    assert ("SafetyInvariantRunner", "RunLauncher") in pairs
    assert ("ApprovalLedger", "governance") in pairs
    assert ("ArtifactIndex", "EvidenceNavigator") in pairs
    assert ("OperatorStatusBoard", "inner_map") in pairs
