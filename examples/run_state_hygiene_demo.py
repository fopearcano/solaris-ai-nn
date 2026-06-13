#!/usr/bin/env python3
"""State hygiene demo: archive old reports, quarantine corrupt records.

    python examples/run_state_hygiene_demo.py

Writes an oversized log and a corrupt JSONL into the state directory, then
runs state hygiene: the corrupt file is quarantined and the old report is
archived -- both moved (never deleted), and never touching source files.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.autoregeneration import StateHygieneManager


def main() -> None:
    parser = argparse.ArgumentParser(description="State hygiene demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/state_hygiene")
    args = parser.parse_args()

    root = Path(args.state_dir)
    root.mkdir(parents=True, exist_ok=True)
    (root / "old_report.jsonl").write_text(
        "".join('{"event": %d}\n' % i for i in range(50)), encoding="utf-8")
    (root / "corrupt_trace.jsonl").write_text(
        '{"ok": 1}\n{ this is not valid json\n', encoding="utf-8")

    sh = StateHygieneManager(state_dir=root, max_file_bytes=10)
    scan = sh.scan()

    print("=" * 70)
    print("Solaris-AI-NN -- state hygiene (archive/quarantine, never delete)")
    print("=" * 70)
    print(f"state dir:            {root}")
    print(f"oversized files:      {scan['oversized']}")
    print(f"corrupt files:        {scan['corrupt']}")

    quarantined = sh.quarantine_file("corrupt_trace.jsonl",
                                     reason="unparseable JSONL")
    archived = sh.archive_file("old_report.jsonl")
    print(f"quarantined ->        {quarantined}")
    print(f"archived ->           {archived}")
    print(f"quarantine/ exists:   {(root / 'quarantine').exists()}")
    print(f"archive/ exists:      {(root / 'archive').exists()}")
    print(f"audit log exists:     {(root / 'repair_audit.jsonl').exists()}")
    print()
    print("note: corrupted/old files are MOVED into quarantine/ and archive/, "
          "never deleted; evidence files (incidents, governance audit) are "
          "never archived without a summary; source files are untouched.")


if __name__ == "__main__":
    main()
