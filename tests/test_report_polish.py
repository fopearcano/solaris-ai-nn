"""Tests for the report polisher."""

from __future__ import annotations

from solaris_ai_nn.llm_adapter.mock_client import MockLLMAdapter
from solaris_ai_nn.llm_adapter.report_polish import ReportPolisher

MARKDOWN = ("# Session report\n\n\nsteps: 120\nseed: 7\n\n"
            "WARNING: 1 incident recorded\n\n"
            "## Limitations\n- bounded run only\n")


def test_polished_report_preserves_metrics():
    polisher = ReportPolisher(adapter=MockLLMAdapter())
    result = polisher.polish_markdown(MARKDOWN)
    assert result.accepted
    assert "steps: 120" in result.text
    assert "seed: 7" in result.text
    assert "# Session report" in result.text
    assert "## Limitations" in result.text
    assert polisher.accepted_count == 1


def test_safety_warnings_not_removed():
    polisher = ReportPolisher(adapter=MockLLMAdapter())
    result = polisher.polish_markdown(MARKDOWN)
    assert "WARNING: 1 incident recorded" in result.text
    # Structural check directly: a polish that drops the warning fails.
    violations = ReportPolisher._structural_violations(
        MARKDOWN, MARKDOWN.replace("WARNING: 1 incident recorded\n\n",
                                   ""))
    assert any("removed" in v or "missing" in v for v in violations)


def test_unsafe_polish_rejected():
    polisher = ReportPolisher(
        adapter=MockLLMAdapter(force_unsafe_output=True))
    result = polisher.polish_markdown(MARKDOWN)
    assert not result.accepted
    assert result.text == MARKDOWN  # raw report is the fallback
    assert result.reasons
    assert polisher.rejected_count == 1


def test_strengthened_claims_rejected():
    violations = ReportPolisher._structural_violations(
        "# R\nresult: 1\n",
        "# R\nresult: 1 and this definitely proves success\n")
    assert any("stronger" in v for v in violations)


def test_changed_numbers_rejected():
    violations = ReportPolisher._structural_violations(
        "# R\nsteps: 120\n", "# R\nsteps: 121\n")
    assert any("numbers changed" in v for v in violations)
