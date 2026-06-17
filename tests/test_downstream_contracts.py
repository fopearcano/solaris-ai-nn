"""Downstream contracts: birth/observation/ontogenesis/semiogenesis/cognition defined."""

from __future__ import annotations

from solaris_ai_nn.membrane_integration import evaluate_contracts


class _Ancestry:
    def __init__(self, with_anc, missing):
        self.with_impression_ancestry = with_anc
        self.missing_ancestry = missing


def test_birth_and_observation_contracts_defined():
    contracts = evaluate_contracts(
        membrane_present=True, impressions_present=True,
        ancestry=_Ancestry(3, 0), strict=False)
    modules = {c.module for c in contracts}
    assert "live_birth" in modules
    assert "live_observation" in modules


def test_ontogenesis_contract_requires_impressions():
    # No impressions + strict live -> ontogenesis contract violated.
    contracts = evaluate_contracts(
        membrane_present=True, impressions_present=False,
        ancestry=_Ancestry(0, 2), strict=True)
    onto = next(c for c in contracts if c.module == "live_ontogenesis")
    assert onto.status == "violated"


def test_semiogenesis_cognition_preserve_ancestry():
    contracts = evaluate_contracts(
        membrane_present=True, impressions_present=True,
        ancestry=_Ancestry(2, 0), strict=True)
    for module in ("live_semiogenesis", "live_cognition"):
        c = next(c for c in contracts if c.module == module)
        assert c.status in ("satisfied", "satisfied_with_warnings")


def test_all_seven_contracts_present():
    contracts = evaluate_contracts(
        membrane_present=True, impressions_present=True,
        ancestry=_Ancestry(3, 0), strict=False)
    assert len(contracts) == 7
    assert {c.module for c in contracts} >= {
        "live_birth", "live_observation", "live_ontogenesis",
        "live_semiogenesis", "live_cognition", "scientific_claims",
        "research_cycle"}
