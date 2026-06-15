"""OperatorQueryRouter: list/plan work; unsafe blocked; evidence local only."""

from __future__ import annotations

import os

from solaris_ai_nn.operator_console import (
    OperatorConsoleConfig,
    OperatorQueryRouter,
    ProfileCatalog,
)


def _router(tmp_path, **kw):
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"))
    return OperatorQueryRouter(config=cfg, catalog=ProfileCatalog(), **kw)


def test_list_profiles_works(tmp_path):
    result = _router(tmp_path).route("list_profiles")
    assert result.ok
    assert result.data["runnable"]
    assert result.data["blocked"]


def test_plan_profile_works(tmp_path):
    result = _router(tmp_path).route("plan_profile",
                                     profile_id="safety_fast_check")
    assert result.ok
    assert result.data["external_authority"] is False


def test_unsafe_run_query_blocked(tmp_path):
    # No launcher attached -> the router runs nothing on its own.
    result = _router(tmp_path).route("run_profile_if_allowed",
                                     profile_id="minimal_smoke",
                                     operator_confirmed=True)
    assert result.refused
    assert result.ok is False


def test_unknown_query_refused(tmp_path):
    result = _router(tmp_path).route("delete_all_evidence")
    assert result.refused


def test_evidence_query_local_only(tmp_path):
    base = str(tmp_path / "op")
    os.makedirs(base, exist_ok=True)
    with open(os.path.join(base, "research_report.json"), "w",
              encoding="utf-8") as fh:
        fh.write('{"summary": "safety baseline"}')
    result = _router(tmp_path).route("search_evidence", keyword="safety")
    assert result.ok
    assert result.data["external_search"] is False
