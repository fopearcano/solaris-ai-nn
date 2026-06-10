"""Tests for ArtifactRotationPolicy."""

from __future__ import annotations

import gzip

from solaris_ai_nn.ops.artifact_rotation import ArtifactRotationPolicy


def _setup(tmp_path):
    allowed = tmp_path / "state"
    allowed.mkdir()
    big = allowed / "trace_events.jsonl"
    big.write_text("x" * 2048)
    return allowed, big


def test_dry_run_does_not_delete(tmp_path):
    allowed, big = _setup(tmp_path)
    policy = ArtifactRotationPolicy([allowed], compress_jsonl_over_bytes=1024)
    report = policy.dry_run()
    assert str(big) in report["would_compress"]
    assert big.exists() and big.stat().st_size == 2048  # untouched


def test_rotation_compresses_inside_allowed_dir(tmp_path):
    allowed, big = _setup(tmp_path)
    policy = ArtifactRotationPolicy([allowed], compress_jsonl_over_bytes=1024)
    report = policy.rotate()
    assert len(report["compressed"]) == 1
    archive = report["compressed"][0]
    with gzip.open(archive, "rb") as fh:
        assert fh.read() == b"x" * 2048
    assert big.exists() and big.stat().st_size == 0  # truncated, not deleted
    assert report["errors"] == []


def test_outside_path_rejected(tmp_path):
    allowed, _ = _setup(tmp_path)
    outside = tmp_path / "outside.jsonl"
    outside.write_text("y" * 4096)
    policy = ArtifactRotationPolicy([allowed], compress_jsonl_over_bytes=1024)
    plan = policy.scan()
    assert str(outside) not in plan["compress"]  # never even considered
    policy.rotate()
    assert outside.read_text() == "y" * 4096  # untouched


def test_python_files_never_touched(tmp_path):
    allowed, _ = _setup(tmp_path)
    py = allowed / "module.py"
    py.write_text("print('hi')" * 500)
    policy = ArtifactRotationPolicy([allowed], compress_jsonl_over_bytes=10)
    policy.rotate()
    assert py.exists() and "print" in py.read_text()


def test_trim_keeps_newest_archives(tmp_path):
    allowed, _ = _setup(tmp_path)
    import time
    for i in range(5):
        p = allowed / f"trace_events.jsonl.2024010{i}000000.gz"
        p.write_bytes(b"z")
        time.sleep(0.01)
    policy = ArtifactRotationPolicy([allowed], keep_archives=2,
                                    compress_jsonl_over_bytes=10**9)
    report = policy.rotate()
    assert len(report["trimmed"]) == 3
    remaining = list(allowed.glob("*.gz"))
    assert len(remaining) == 2
