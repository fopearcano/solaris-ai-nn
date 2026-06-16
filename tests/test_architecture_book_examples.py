"""Architecture book examples run end to end without hanging."""

from __future__ import annotations

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(script, tmp_path, extra=None):
    path = os.path.join(_ROOT, "examples", script)
    cmd = [sys.executable, path, "--state-dir", str(tmp_path)]
    cmd += extra or []
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_architecture_book_demo_runs(tmp_path):
    out = _run("run_architecture_book_demo.py", tmp_path,
               ["--docs-dir", str(tmp_path / "wp")])
    assert "Architecture book demo" in out
    assert "published / git       : False / False" in out


def test_whitepaper_builder_demo_runs(tmp_path):
    out = _run("run_whitepaper_builder_demo.py", tmp_path,
               ["--docs-dir", str(tmp_path / "wp")])
    assert "Whitepaper builder demo" in out
    assert "does not prove" in out.lower() or "research architecture" in out.lower()


def test_diagram_builder_demo_runs(tmp_path):
    out = _run("run_diagram_builder_demo.py", tmp_path)
    assert "Diagram builder demo" in out
    assert "mermaid" in out


def test_glossary_builder_demo_runs(tmp_path):
    out = _run("run_glossary_builder_demo.py", tmp_path)
    assert "Glossary builder demo" in out
    assert "metaphor" in out.lower()


def test_documentation_index_demo_runs(tmp_path):
    out = _run("run_documentation_index_demo.py", tmp_path,
               ["--docs-dir", str(tmp_path / "wp")])
    assert "Documentation index demo" in out
    assert "missing documents" in out.lower()
