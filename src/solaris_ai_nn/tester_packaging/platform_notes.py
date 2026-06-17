"""Platform notes builder -- per-OS local install notes (no admin/root, no global).

:class:`PlatformNotesBuilder` writes Windows/macOS/Linux notes covering venv activation,
path separators, the PowerShell execution-policy note, terminal permissions, and the
no-admin/no-global-install guidance.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


class PlatformKind:
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"

    ALL = (WINDOWS, MACOS, LINUX, UNKNOWN)


@dataclass
class PlatformNote:
    """One platform's install notes."""

    kind: str
    lines: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        title = {"windows": "Windows", "macos": "macOS",
                 "linux": "Linux"}.get(self.kind, "Unknown")
        out = [f"# {title} Notes", "",
               "_Local editable install only. No admin/root is required and no "
               "global install is recommended._", ""]
        out += [f"- {l}" for l in self.lines]
        return "\n".join(out)

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "lines": list(self.lines)}


_NOTES = {
    PlatformKind.WINDOWS: [
        "Create the venv: `python -m venv .venv`",
        "Activate (PowerShell): `.venv\\Scripts\\Activate.ps1`",
        "If activation is blocked, run `Set-ExecutionPolicy -Scope Process "
        "RemoteSigned` first (process-scoped; no admin needed).",
        "Use backslash path separators in PowerShell; the CLI accepts forward "
        "slashes in `--state-dir` arguments.",
        "Install locally: `pip install -e .` (no global/system install).",
        "No administrator privileges are required.",
    ],
    PlatformKind.MACOS: [
        "Create the venv: `python3 -m venv .venv`",
        "Activate: `source .venv/bin/activate`",
        "Install locally: `pip install -e .` (no `sudo`, no global install).",
        "Use forward-slash paths; quote paths that contain spaces.",
        "Grant the terminal file access if macOS prompts for the working folder.",
        "No root privileges are required.",
    ],
    PlatformKind.LINUX: [
        "Create the venv: `python3 -m venv .venv`",
        "Activate: `source .venv/bin/activate`",
        "Install locally: `pip install -e .` (no `sudo`, no global install).",
        "Use forward-slash paths.",
        "Run from a folder you own so state dirs are writable.",
        "No root privileges are required.",
    ],
}


@dataclass
class PlatformNotesBuilder:
    """Builds the per-platform install notes."""

    def build(self) -> List[PlatformNote]:
        return [PlatformNote(kind=k, lines=list(_NOTES[k]))
                for k in (PlatformKind.WINDOWS, PlatformKind.MACOS,
                          PlatformKind.LINUX)]

    def write(self, platforms_dir: str) -> Dict[str, str]:
        os.makedirs(platforms_dir, exist_ok=True)
        written: Dict[str, str] = {}
        names = {PlatformKind.WINDOWS: "WINDOWS_NOTES.md",
                 PlatformKind.MACOS: "MACOS_NOTES.md",
                 PlatformKind.LINUX: "LINUX_NOTES.md"}
        for note in self.build():
            path = os.path.join(platforms_dir, names[note.kind])
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(note.to_markdown())
            written[note.kind] = path
        return written
