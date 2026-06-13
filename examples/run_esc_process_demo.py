#!/usr/bin/env python3
"""Esc process demo: an instability signal, not panic.

    python examples/run_esc_process_demo.py

Builds a context with repeated unresolved high-severity instability
(Mysterium saturation, runaway complexity, contradiction explosion), shows
the Esc trigger and its bounded stabilization responses, and confirms Esc
cannot execute real-world actions.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.logos_complexity import (
    EscProcess,
    LogosComplexityEngine,
    LogosComplexityReportBuilder,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Esc process demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/esc_process")
    args = parser.parse_args()

    esc = EscProcess()
    calm = esc.evaluate({"mysterium_pressure": 0.2})
    unstable = esc.evaluate({
        "unresolved_high_severity_count": 3,
        "mysterium_pressure": 0.96,
        "complexity": {"band": "overloaded"},
        "world_model": {"contradiction_edges": ["a", "b", "c", "d", "e"]},
        "executive": {"no_safe_action_count": 6}})

    print("=" * 70)
    print("Solaris-AI-NN -- Esc process (instability signal, not emotion)")
    print("=" * 70)
    print(f"calm context  -> triggered={calm.triggered}")
    print(f"unstable      -> triggered={unstable.triggered} "
          f"level={unstable.level}")
    print(f"triggers:       {unstable.triggers}")
    print(f"responses:      {unstable.responses}")
    print()

    engine = LogosComplexityEngine(state_dir=args.state_dir)
    engine.tick({
        "world_model": {"contradiction_edges": ["a|c|b", "d|c|e", "f|c|g",
                                                "h|c|i", "j|c|k"],
                        "prediction_accuracy": 0.1},
        "mysterium_pressure": 0.97, "state_dir": args.state_dir})
    builder = LogosComplexityReportBuilder(engine)
    paths = builder.save(Path(args.state_dir) / "report.json",
                         Path(args.state_dir) / "report.md")
    print(f"report: {paths['markdown']} (claim guard safe: "
          f"{paths['claim_guard']['safe']})")
    print()
    print("note: Esc is an operational instability signal, not panic and not "
          "an emotion. It can request stabilization, latent replay, or "
          "auto-regeneration; it can never execute real-world actions or "
          "bypass safety.")


if __name__ == "__main__":
    main()
