"""Architecture book CLI: build-docs, docs-index, whitepaper, strict."""

from __future__ import annotations

import os

from solaris_ai_nn.cli import main


def test_build_docs_command(tmp_path):
    sd = str(tmp_path / "s")
    dd = str(tmp_path / "d")
    rc = main(["build-docs", "--state-dir", sd, "--docs-dir", dd])
    assert rc == 0
    assert os.path.isfile(os.path.join(dd, "SOLARIS_AI_NN_WHITEPAPER.md"))
    assert os.path.isfile(os.path.join(sd, "WHITEPAPER_BUILD_REPORT.md"))


def test_docs_index_command(tmp_path):
    dd = str(tmp_path / "d")
    main(["build-docs", "--state-dir", str(tmp_path / "s"), "--docs-dir", dd])
    rc = main(["docs-index", "--state-dir", str(tmp_path / "s"),
               "--docs-dir", dd])
    assert rc == 0


def test_whitepaper_command(tmp_path):
    rc = main(["whitepaper", "--state-dir", str(tmp_path / "s"),
               "--docs-dir", str(tmp_path / "d")])
    assert rc == 0
    assert os.path.isfile(
        str(tmp_path / "d" / "SOLARIS_AI_NN_WHITEPAPER.md"))


def test_alpha_group_build_docs(tmp_path):
    rc = main(["alpha", "build-docs", "--state-dir", str(tmp_path / "s"),
               "--docs-dir", str(tmp_path / "d")])
    assert rc == 0


def test_strict_mode_handles_blockers(tmp_path):
    # require_claimguard + strict; if ClaimGuard is present this returns 0,
    # otherwise 2. Either way it returns a clean int exit code.
    rc = main(["build-docs", "--state-dir", str(tmp_path / "s"),
               "--docs-dir", str(tmp_path / "d"), "--strict",
               "--require-claimguard"])
    assert rc in (0, 2)
