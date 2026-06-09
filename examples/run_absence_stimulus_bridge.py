#!/usr/bin/env python3
"""Run the absence-stimulus bridge experiment.

Demonstrates that the neural substrate keeps evolving during silence by
processing synthesised "I exist!" absence stimuli through the
:class:`SolarisNeuralBridge`, mirroring Solaris_Ai's AION/Impulse core.

Usage:

    python examples/run_absence_stimulus_bridge.py
    python examples/run_absence_stimulus_bridge.py 60 60   # presence/silence steps
"""

from __future__ import annotations

import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.absence_stimulus_bridge import run_absence_stimulus_bridge


def main() -> None:
    presence = int(sys.argv[1]) if len(sys.argv) > 1 else 45
    silence = int(sys.argv[2]) if len(sys.argv) > 2 else 45
    run_absence_stimulus_bridge(presence_steps=presence, silence_steps=silence, verbose=True)


if __name__ == "__main__":
    main()
