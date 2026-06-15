#!/usr/bin/env python3
"""Perspective/continuity demo: perspective shift, anchors, break + recovery.

    python examples/run_perspective_continuity_demo.py --state-dir .solaris_ai_nn_self_boundary/test_perspective_continuity

Shows a perspective frame shift, continuity anchors, and a continuity break that is
recovered without erasing the break history.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.self_boundary import (
    ContinuityAnchorType,
    ContinuityBreakType,
    OrganismicContinuity,
    PerspectiveFrame,
    SensoriumPerspective,
)


def main():
    parser = argparse.ArgumentParser(description="Perspective/continuity demo")
    parser.add_argument(
        "--state-dir", type=str,
        default=".solaris_ai_nn_self_boundary/test_perspective_continuity")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    perspective = SensoriumPerspective()
    perspective.update(PerspectiveFrame(active_modality="radio_frequency",
                                        dominant_receptor="radio_frequency",
                                        attention_focus="novelty_need"))
    shift = perspective.update(PerspectiveFrame(active_modality="vibration",
                                                dominant_receptor="vibration",
                                                attention_focus="rhythm_need"),
                               reason="dominant modality changed")

    continuity = OrganismicContinuity()
    continuity.anchor(ContinuityAnchorType.HEARTBEAT, "tick:0")
    continuity.anchor(ContinuityAnchorType.RECEPTOR, "rf")
    brk = continuity.record_break(ContinuityBreakType.SOURCE_SILENCE,
                                  detail="source went silent")
    continuity.recover(brk.break_id, ContinuityAnchorType.SENSORY_FIELD,
                       detail="source resumed")

    print("=== Perspective/continuity demo ===")
    print(f"perspective shift     : {shift.from_signature} -> "
          f"{shift.to_signature}")
    print(f"attention rec.        : {perspective.attention_recommendation()}")
    print(f"continuity anchors    : {len(continuity.anchors)}")
    print(f"continuity breaks     : {len(continuity.breaks)} "
          f"(recovered={continuity.breaks[0].recovered})")
    print(f"break still in log    : "
          f"{any(b.break_id == brk.break_id for b in continuity.breaks)}")
    print(f"continuity score      : {continuity.continuity_score()}")
    print("note: continuity is trace continuity, not biological life; a "
          "recovered break is still retained in the break history.")


if __name__ == "__main__":
    main()
