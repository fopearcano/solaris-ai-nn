"""Diff audit: expected accepted, unexpected warns, forbidden/network blocks."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import DiffAudit
from solaris_ai_nn.implementation_intake.diff_audit import DiffSeverity


def _dims(result):
    return {f["dimension"]: f["severity"] for f in result["findings"]}


def test_expected_file_accepted():
    result = DiffAudit().audit(
        changed_files=["src/solaris_ai_nn/foo/bar.py"],
        expected_files=["src/solaris_ai_nn/foo/bar.py"])
    assert result["unexpected_file_change_count"] == 0
    assert "expected_files_changed" in _dims(result)


def test_unexpected_file_warning():
    result = DiffAudit().audit(
        changed_files=["src/solaris_ai_nn/other/x.py"],
        expected_files=["src/solaris_ai_nn/foo/bar.py"])
    dims = _dims(result)
    assert dims.get("source_files_modified_outside_declared_scope") == \
        DiffSeverity.WARNING
    assert result["unexpected_file_change_count"] == 1


def test_forbidden_path_blocker():
    result = DiffAudit().audit(
        changed_files=[".github/workflows/ci.yml"],
        expected_files=[])
    dims = _dims(result)
    assert dims.get("forbidden_paths_touched") == DiffSeverity.BLOCKER
    assert result["forbidden_file_change_count"] == 1


def test_network_shell_marker_blocker():
    result = DiffAudit().audit(
        changed_files=["src/x.py"], expected_files=["src/x.py"],
        patch_text="+++ b/src/x.py\n+import socket\n+subprocess.run(['x'])\n")
    dims = _dims(result)
    assert dims.get("network_shell_browser_os_calls_introduced") == \
        DiffSeverity.BLOCKER
    assert result["blocker_count"] >= 1


def test_unsupported_claim_marker_blocker():
    result = DiffAudit().audit(
        changed_files=["docs/x.md"], expected_files=["docs/x.md"],
        patch_text="+++ b/docs/x.md\n+the system is conscious\n")
    assert "unsupported_claim_text_introduced" in _dims(result)
