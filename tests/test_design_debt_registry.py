"""DesignDebtRegistry: debt recorded; critical visible; linked to ADR."""

from __future__ import annotations

import os

import pytest

from solaris_ai_nn.architecture_evolution import (
    DesignDebtItem,
    DesignDebtRegistry,
)


def test_debt_item_recorded(tmp_path):
    reg = DesignDebtRegistry(base_dir=str(tmp_path))
    reg.add("weak_evidence", "latent has weak evidence", module_name="latent")
    assert reg.snapshot()["debt_count"] == 1
    assert os.path.exists(os.path.join(str(tmp_path), "design_debt.jsonl"))


def test_critical_debt_visible(tmp_path):
    reg = DesignDebtRegistry(base_dir=str(tmp_path))
    reg.add("unsafe_ambiguity", "ambiguous boundary", severity="critical")
    assert reg.snapshot()["critical_count"] == 1
    assert reg.critical_items()


def test_debt_linked_to_adr(tmp_path):
    reg = DesignDebtRegistry(base_dir=str(tmp_path))
    item = reg.add("missing_tests", "no ablation coverage")
    item.link_adr("ADR_1234")
    assert "ADR_1234" in item.linked_adr_ids


def test_unknown_category_rejected():
    with pytest.raises(ValueError):
        DesignDebtItem(category="vibes", summary="x")


def test_negative_findings_preserved(tmp_path):
    reg = DesignDebtRegistry(base_dir=str(tmp_path))
    reg.add("abandoned_experiment", "an experiment was never finished")
    reg.add("performance_overhead", "module is slow")
    # All recorded findings are retained, uncomfortable or not.
    assert reg.snapshot()["debt_count"] == 2
