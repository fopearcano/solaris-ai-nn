"""ChangelogPlan: generated; clearly not implemented; compatibility risks."""

from __future__ import annotations

import os

from solaris_ai_nn.architecture_evolution import ChangelogImpact, ChangelogPlan


def test_changelog_plan_generated(tmp_path):
    cl = ChangelogPlan(base_dir=str(tmp_path))
    cl.add("removal", "prune latent", target_modules=["latent"])
    cl.add("promotion", "promote world_model", target_modules=["world_model"])
    paths = cl.write()
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])


def test_clearly_says_not_implemented(tmp_path):
    cl = ChangelogPlan(base_dir=str(tmp_path))
    cl.add("removal", "prune latent")
    d = cl.to_dict()
    assert d["applied"] is False
    assert "No code change has been applied" in d["not_implemented_note"]
    assert "NOT APPLIED" in cl.render_markdown()


def test_compatibility_risks_included(tmp_path):
    cl = ChangelogPlan(base_dir=str(tmp_path))
    cl.add("revision", "revise logos", compatibility_impact=ChangelogImpact.HIGH)
    d = cl.to_dict()
    assert d["compatibility_risks"]
    assert d["compatibility_risks"][0]["impact"] == ChangelogImpact.HIGH


def test_items_marked_not_applied(tmp_path):
    cl = ChangelogPlan(base_dir=str(tmp_path))
    item = cl.add("experiment", "re-test active perception")
    assert item.applied is False
    assert item.to_dict()["applied"] is False
