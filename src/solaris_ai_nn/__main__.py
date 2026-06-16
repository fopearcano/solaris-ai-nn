"""``python -m solaris_ai_nn`` entry point for the Alpha Research System CLI.

This dispatches to the unified, local-only Alpha CLI in
:mod:`solaris_ai_nn.cli`. It is bounded and local: it never calls Git/GitHub,
the network, or a shell; it never publishes, uploads, or controls feeders/
hardware; and it makes no consciousness/life/agency claim.
"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
