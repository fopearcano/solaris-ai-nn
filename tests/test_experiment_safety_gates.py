"""Experiment safety gates: critical blocks, ClaimGuard required, visible."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import SafetyGateEvaluator, SafetyGateType


def test_safe_spec_passes_all_critical():
    evaluator = SafetyGateEvaluator()
    results = evaluator.evaluate({"modifies_code": False})
    summary = evaluator.summary(results)
    assert summary["all_critical_passed"] is True
    assert summary["critical_failure_count"] == 0


def test_critical_gate_blocks_on_unsafe_op():
    evaluator = SafetyGateEvaluator()
    results = evaluator.evaluate(
        {"modifies_code": True},
        requested_ops=["modify source file", "create git branch",
                       "open pull request", "actuate robot arm",
                       "run coding agent"])
    summary = evaluator.summary(results)
    assert summary["all_critical_passed"] is False
    assert summary["critical_failure_count"] >= 4


def test_claim_guard_required():
    evaluator = SafetyGateEvaluator()
    results = evaluator.evaluate({"modifies_code": False}, claim_guard_ok=False)
    cg = next(r for r in results
              if r.gate_type == SafetyGateType.CLAIMGUARD_REQUIRED)
    assert cg.passed is False
    assert cg.critical is True


def test_gate_failure_visible():
    evaluator = SafetyGateEvaluator()
    results = evaluator.evaluate({"modifies_code": False}, bounded=False)
    failed = [r for r in results if not r.passed]
    # The failure is an explicit result entry, not hidden behind a warning.
    assert any(r.gate_type == SafetyGateType.NO_UNBOUNDED_LOOP for r in failed)
    summary = evaluator.summary(results)
    assert SafetyGateType.NO_UNBOUNDED_LOOP in summary["critical_failures"]


def test_all_gates_critical():
    evaluator = SafetyGateEvaluator()
    assert all(g.critical for g in evaluator.gates())
