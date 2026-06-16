"""Alpha operator runbook: generated, forbidden interpretations, stop conditions."""

from __future__ import annotations

from solaris_ai_nn.alpha_system import AlphaRunbookBuilder


def test_runbook_generated():
    runbook = AlphaRunbookBuilder().build(".solaris_ai_nn_alpha")
    d = runbook.to_dict()
    assert d["steps"]
    md = runbook.render_md()
    assert "Alpha Operator Runbook" in md


def test_forbidden_interpretations_included():
    runbook = AlphaRunbookBuilder().build(".solaris_ai_nn_alpha")
    d = runbook.to_dict()
    text = " ".join(d["forbidden_interpretations"]).lower()
    assert "consciousness" in text
    assert "agency" in text
    assert "ground truth" in text


def test_stop_conditions_included():
    runbook = AlphaRunbookBuilder().build(".solaris_ai_nn_alpha")
    d = runbook.to_dict()
    assert d["stop_conditions"]
    assert any("blocker" in s for s in d["stop_conditions"])


def test_what_it_is_not_included():
    runbook = AlphaRunbookBuilder().build(".solaris_ai_nn_alpha")
    text = " ".join(runbook.to_dict()["what_it_is_not"]).lower()
    assert "not a product release" in text
    assert "not consciousness evidence" in text


def test_runbook_steps_not_executed():
    runbook = AlphaRunbookBuilder().build(".solaris_ai_nn_alpha")
    assert all(s["executed"] is False for s in runbook.to_dict()["steps"])
