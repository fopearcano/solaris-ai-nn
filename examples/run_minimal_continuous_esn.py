#!/usr/bin/env python3
"""Run the minimal continuous-ESN experiment.

Usage:

    python examples/run_minimal_continuous_esn.py
    python examples/run_minimal_continuous_esn.py 3000   # custom step count

This script adds ``src/`` to ``sys.path`` so it runs from a fresh checkout
without installation. If you have run ``pip install -e .`` you can instead use
the ``solaris-nn-demo`` console command.
"""

from __future__ import annotations

import os
import sys

# Allow running directly from a source checkout (no install required).
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.minimal_continuous_esn import run_minimal_continuous_esn


def main() -> None:
    max_steps = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    run_minimal_continuous_esn(max_steps=max_steps, verbose=True)


if __name__ == "__main__":
    main()
