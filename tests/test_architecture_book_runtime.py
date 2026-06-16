"""Architecture book runtime: bounded, docs generated, no publish/Git/exec."""

from __future__ import annotations

import inspect
import os


from solaris_ai_nn.architecture_book import ArchitectureBookRuntime


def test_bounded_runtime(tmp_path):
    rt = ArchitectureBookRuntime(state_dir=str(tmp_path / "s"),
                                 docs_dir=str(tmp_path / "d"))
    assert rt.run()["refused"] is False


def test_unbounded_refused(tmp_path):
    rt = ArchitectureBookRuntime(state_dir=str(tmp_path / "s"),
                                 docs_dir=str(tmp_path / "d"), max_runtime_s=0)
    assert rt.run()["refused"] is True


def test_docs_generated(tmp_path):
    docs = str(tmp_path / "d")
    rt = ArchitectureBookRuntime(state_dir=str(tmp_path / "s"), docs_dir=docs)
    rt.run()
    for fn in ("SOLARIS_AI_NN_TECHNICAL_OVERVIEW.md",
               "SOLARIS_AI_NN_WHITEPAPER.md",
               "SOLARIS_AI_NN_ARCHITECTURE_BOOK.md",
               "SOLARIS_AI_NN_MODULE_MAP.md", "SOLARIS_AI_NN_GLOSSARY.md",
               "SOLARIS_AI_NN_APPENDICES.md",
               "SOLARIS_AI_NN_DOCUMENTATION_INDEX.md"):
        assert os.path.isfile(os.path.join(docs, fn))


def test_status_flags_no_publish_git(tmp_path):
    rt = ArchitectureBookRuntime(state_dir=str(tmp_path / "s"),
                                 docs_dir=str(tmp_path / "d"))
    rt.run()
    st = rt.documentation_status()
    assert st["published"] is False
    assert st["uploaded"] is False
    assert st["runs_git"] is False
    assert st["calls_github"] is False


def test_no_publish_git_exec_in_source():
    import solaris_ai_nn.architecture_book.book_runtime as runtime

    src = inspect.getsource(runtime)
    assert "subprocess" not in src
    assert "import requests" not in src
    assert "os.system" not in src
    assert "urllib" not in src
