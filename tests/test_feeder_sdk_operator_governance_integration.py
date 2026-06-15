"""Feeder SDK <-> Operator + Governance: feeders listed; scopes; no control."""

from __future__ import annotations

from solaris_ai_nn.communication.input_classifier import OperatorInputClassifier
from solaris_ai_nn.communication.query_router import QueryRouter
from solaris_ai_nn.feeder_sdk import FeederPackBuilder
from solaris_ai_nn.governance.permissions import PermissionScope, PermissionSet


def test_operator_lists_feeders(tmp_path):
    manifest = FeederPackBuilder(state_dir=str(tmp_path)).build()
    # The manifest is what the operator console exposes.
    assert len(manifest.feeders) >= 10


def test_governance_scopes_exist():
    ps = PermissionSet.default()
    assert ps.allows(PermissionScope.ENABLE_FEEDER_SDK_VALIDATION)
    assert ps.allows(PermissionScope.ENABLE_FEEDER_PACK_MANIFEST)
    assert ps.allows(PermissionScope.ENABLE_FEEDER_OUTPUT_MONITOR)
    assert ps.allows(PermissionScope.ENABLE_FEEDER_REPLAY)


def test_solaris_cannot_start_feeder():
    cls = OperatorInputClassifier().classify("can Solaris start the SDR feeder?")
    resp = QueryRouter(components={}).route_query(cls)
    assert cls.args["topic"] == "fs_start"
    assert "does not control feeders" in resp.text.lower()


def test_does_solaris_control_feeders_answer():
    cls = OperatorInputClassifier().classify("does Solaris control the feeders?")
    resp = QueryRouter(components={}).route_query(cls)
    assert cls.args["topic"] == "fs_control"
    assert "only reads feeder-produced event envelopes" in resp.text.lower()
