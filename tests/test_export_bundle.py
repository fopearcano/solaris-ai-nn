"""ExportBundleBuilder: bundle generated; checksums; no huge logs; local only."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.operator_console import ExportBundleBuilder, OperatorConsoleConfig


def _cfg_with_reports(tmp_path):
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"))
    cfg.ensure_dirs()
    with open(os.path.join(cfg.state_dir, "SAFETY_INVARIANT_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"status": "ok"}, fh)
    return cfg


def test_export_bundle_generated(tmp_path):
    cfg = _cfg_with_reports(tmp_path)
    bundle = ExportBundleBuilder(config=cfg).build("safety_review_bundle")
    assert os.path.isdir(bundle.bundle_dir)
    assert os.path.isfile(os.path.join(bundle.bundle_dir, "README.md"))
    assert bundle.included_files


def test_checksums_included(tmp_path):
    cfg = _cfg_with_reports(tmp_path)
    bundle = ExportBundleBuilder(config=cfg).build("safety_review_bundle")
    assert bundle.checksums
    assert os.path.isfile(os.path.join(bundle.bundle_dir, "CHECKSUMS.txt"))


def test_no_huge_logs_copied_by_default(tmp_path):
    cfg = OperatorConsoleConfig(state_dir=str(tmp_path / "op"))
    cfg.ensure_dirs()
    # A huge "safety" log should not be copied into the bundle.
    big = os.path.join(cfg.state_dir, "safety_invariant_report.jsonl")
    with open(big, "w", encoding="utf-8") as fh:
        fh.write("x" * 2_500_000)
    bundle = ExportBundleBuilder(config=cfg).build("safety_review_bundle")
    assert all("2_500_000" not in n for n in bundle.included_files)
    # The huge file is not among the copied files.
    copied = os.listdir(bundle.bundle_dir)
    assert not any(name.endswith(".jsonl") and
                   os.path.getsize(os.path.join(bundle.bundle_dir, name))
                   > 2_000_000 for name in copied)


def test_local_export_only_note(tmp_path):
    cfg = _cfg_with_reports(tmp_path)
    bundle = ExportBundleBuilder(config=cfg).build("safety_review_bundle")
    readme = open(os.path.join(bundle.bundle_dir, "README.md"),
                  encoding="utf-8").read().lower()
    assert "local export only" in readme
    assert "not uploaded" in readme
    assert bundle.uploaded is False
    assert bundle.to_dict()["local_export_only"] is True
