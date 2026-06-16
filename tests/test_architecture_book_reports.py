"""Architecture book reports: build report generated, ClaimGuard status, limits."""

from __future__ import annotations

import os

from solaris_ai_nn.architecture_book import ArchitectureBookRuntime


def _run(tmp_path):
    rt = ArchitectureBookRuntime(state_dir=str(tmp_path / "s"),
                                 docs_dir=str(tmp_path / "d"))
    rt.run()
    return rt


def test_build_report_generated(tmp_path):
    rt = _run(tmp_path)
    out = rt.write_artifacts()
    assert out["markdown"].endswith("WHITEPAPER_BUILD_REPORT.md")
    assert os.path.isfile(out["markdown"])
    assert os.path.isfile(out["json"])


def test_claimguard_status_included(tmp_path):
    rt = _run(tmp_path)
    rt.write_artifacts()
    with open(os.path.join(str(tmp_path / "s"), "WHITEPAPER_BUILD_REPORT.md"),
              encoding="utf-8") as fh:
        text = fh.read().lower()
    assert "claimguard available" in text


def test_limitations_and_disclaimers_included(tmp_path):
    rt = _run(tmp_path)
    rt.write_artifacts()
    with open(os.path.join(str(tmp_path / "s"), "WHITEPAPER_BUILD_REPORT.md"),
              encoding="utf-8") as fh:
        text = fh.read().lower()
    assert "limitations" in text
    assert "no publication occurred" in text
    assert "no git or github operation occurred" in text
    assert "no consciousness/life/agency claim is made" in text


def test_report_claim_guard_safe(tmp_path):
    rt = _run(tmp_path)
    report = rt.write_artifacts()["report"]
    assert report["claim_guard_safe"] is True
