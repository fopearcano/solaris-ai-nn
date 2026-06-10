#!/usr/bin/env python3
"""Attach the NN sidecar to a FAKE Solaris-like runtime (no install needed).

Demonstrates the full integration seam without ``fopearcano/solaris-ai``:
a FakeConscience with a FakeBus emits Stimulus / Push / LogosTension /
MeaningEvent / Reaction signals; the sidecar (observe-only) mirrors them,
updates its substrate, learns from Reactions, and produces suggestions that are
clearly NOT committed.

    python examples/run_fake_solaris_integration.py
    python examples/run_fake_solaris_integration.py --steps 80 --publish
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.experiments.solaris_sidecar_observation import (
    FakeConscience,
    LogosTension,
    MeaningEvent,
    Push,
    Reaction,
    Stimulus,
)
from solaris_ai_nn.integration import SolarisNNSidecar


def main() -> None:
    parser = argparse.ArgumentParser(description="Fake Solaris integration demo")
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--publish", action="store_true",
                        help="leave observe-only mode (suggestions go to the fake bus)")
    args = parser.parse_args()

    conscience = FakeConscience()
    sidecar = SolarisNNSidecar(
        observe_only=not args.publish,
        vocabulary=["light", "noise", "food", "I exist!"],
        seed=args.seed,
    )
    report = sidecar.attach(conscience)
    sidecar.start()

    print("=" * 70)
    print("Solaris-AI-NN -- fake Solaris integration "
          f"(observe_only={not args.publish})")
    print("=" * 70)
    print(f"compatibility: {report.summary()}")
    print("-" * 70)

    payloads = ["light", "noise", "food"]
    for i in range(args.steps):
        beat = i % 5
        if beat == 0:
            conscience.bus.publish(Stimulus(payload=payloads[i % 3], intensity=0.7))
        elif beat == 1:
            conscience.bus.publish(Push(intensity=0.2, direction="reactive"))
        elif beat == 2:
            conscience.bus.publish(LogosTension(division=0.5, union=0.2))
        elif beat == 3:
            conscience.bus.publish(MeaningEvent(meaning="pattern", novelty=0.3))
        else:
            conscience.bus.publish(Reaction(valence=1.0 if i % 2 else -1.0))

    state = sidecar.state
    print(f"signals observed:      {state.signals_observed} "
          f"{dict(state.signals_by_type)}")
    print(f"mirrored:              {len(sidecar.mirror)}")
    print(f"reactions learned:     {state.reactions_learned}")
    print(f"suggestions produced:  {state.suggestions_produced}")
    print(f"suggestions published: {state.suggestions_published}")
    last = sidecar.channel.last(1)
    if last:
        s = last[0]
        print(f"latest suggestion:     {s['payload']['action']} "
              f"(confidence {s['confidence']:.3f}, committed={s['committed']})")
    committed = sum(1 for x in conscience.bus.published
                    if getattr(x, "committed", False))
    print(f"committed actions:     {committed}  (must be 0)")
    print("-" * 70)
    print("sidecar snapshot:")
    print(json.dumps(sidecar.snapshot()["integration"], indent=2, default=str))
    sidecar.detach()
    print("-" * 70)
    print("Detached cleanly. Action authority never left Solaris_Ai (here: the fake).")


if __name__ == "__main__":
    main()
