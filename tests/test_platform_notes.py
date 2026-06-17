"""Platform notes: Windows/macOS/Linux generated; no admin/root required."""

from __future__ import annotations

import os

from solaris_ai_nn.tester_packaging import PlatformKind, PlatformNotesBuilder


def test_windows_notes_generated(tmp_path):
    paths = PlatformNotesBuilder().write(str(tmp_path))
    assert os.path.isfile(paths[PlatformKind.WINDOWS])
    text = open(paths[PlatformKind.WINDOWS]).read()
    assert "Activate.ps1" in text
    assert "ExecutionPolicy" in text


def test_macos_notes_generated(tmp_path):
    paths = PlatformNotesBuilder().write(str(tmp_path))
    assert os.path.isfile(paths[PlatformKind.MACOS])


def test_linux_notes_generated(tmp_path):
    paths = PlatformNotesBuilder().write(str(tmp_path))
    assert os.path.isfile(paths[PlatformKind.LINUX])


def test_no_admin_root_required(tmp_path):
    paths = PlatformNotesBuilder().write(str(tmp_path))
    for path in paths.values():
        text = open(path).read().lower()
        assert "no admin" in text or "no root" in text
        assert "no global install" in text
