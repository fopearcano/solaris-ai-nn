#!/usr/bin/env python3
"""Symbol emergence demo: repetition earns a name, one-offs do not.

    python examples/run_symbol_emergence_demo.py

Repeated signal/action/reaction patterns cross the naming threshold and
become deterministic tokens with evidence; a one-off pattern is ignored;
a counterfactual-grounded candidate is rejected unless marked offline;
and repeated grounding turns a candidate into a stable symbol.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.protolanguage import (
    ProtoLanguageLayer,
    SymbolCandidate,
    SymbolType,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Symbol emergence demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/symbol_emergence")
    args = parser.parse_args()

    layer = ProtoLanguageLayer(state_dir=args.state_dir)
    print("=" * 70)
    print("Solaris-AI-NN -- symbol emergence demo (repetition earns a "
          "name)")
    print("=" * 70)

    scan = layer.process_context({
        "label": "demo_window",
        "repeated_stimulus_patterns": {"light_noise": 6, "one_off": 1},
        "absence_states": {"silence_window": 4},
        "action_reaction_loops": {"rest_recover": 5},
        "mysterium_spikes": {"prediction_miss": 3},
        "need_pressures": {"restore_energy": 4},
    })
    print(f"candidates: {scan['candidates']}  accepted: "
          f"{scan['accepted']}  (the one-off pattern earned nothing)")
    for symbol in sorted(layer.registry.symbols.values(),
                         key=lambda s: s.token):
        print(f"  {symbol.token:26s} <- "
              f"{symbol.grounding_refs[0].reference}")
    print()

    print("counterfactual candidate without offline marking:")
    rejected = layer.emergence.accept_symbol(SymbolCandidate(
        symbol_type=SymbolType.UNKNOWN, grounding_summary="dream_spike",
        evidence_refs=["counterfactual:dream_42"],
        evidence_kind="counterfactual", offline=False))
    print(f"  rejected: {rejected is None}  "
          f"({layer.emergence.rejections[-1]['reason'][:70]})")
    print()

    print("stability through consistent grounding:")
    symbol = layer.registry.find_by_type(SymbolType.HABIT)[0]
    for _ in range(8):
        layer.grounding.ground_symbol(symbol, {
            "context": "quiet_period", "action_tendency": "rest",
            "reaction_valence": 0.6})
    print(f"  {symbol.token}: observations={symbol.observation_count} "
          f"ambiguity={symbol.ambiguity_score} "
          f"stability={symbol.stability_score} stable={symbol.stable}")
    stable = layer.registry.stable()
    print(f"  stable symbols: {[s.token for s in stable]}")
    layer.save_state()
    print()
    print(f"registry persisted: {layer.registry.json_path}")
    print("note: tokens are deterministic generated forms; the debug "
          "labels are secondary, and no symbol is a word in any human "
          "language.")


if __name__ == "__main__":
    main()
