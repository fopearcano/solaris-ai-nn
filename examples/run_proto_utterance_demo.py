#!/usr/bin/env python3
"""Proto-utterance demo: internal sequences with cautious translation.

    python examples/run_proto_utterance_demo.py

Symbols combine into observed sequences, sequences become purposeful
proto-utterances, and the translator renders them as cautious debug text
that is clearly marked as translation -- not speech, not human language.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.protolanguage import ProtoLanguageLayer


def main() -> None:
    parser = argparse.ArgumentParser(description="Proto-utterance demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/proto_utterance")
    args = parser.parse_args()

    layer = ProtoLanguageLayer(state_dir=args.state_dir)
    layer.process_context({
        "absence_states": {"silence_window": 4},
        "need_pressures": {"seek_signal": 4},
        "repeated_actions": {"look": 4},
        "mysterium_spikes": {"prediction_miss": 3},
    })
    tokens = [s.token for s in sorted(layer.registry.symbols.values(),
                                      key=lambda s: s.token)]
    print("=" * 70)
    print("Solaris-AI-NN -- proto-utterance demo (structure, not speech)")
    print("=" * 70)
    print(f"symbols available: {tokens}")
    print()

    # Observe the same symbol stream repeatedly: a sequence forms.
    stream = tokens[:3]
    for i in range(5):
        layer.combinator.observe_sequence(
            stream, {"label": f"window_{i}", "outcome_valence": 0.4})
    repeated = layer.combinator.find_repeated_sequences(3)
    print(f"repeated sequences: {len(repeated)}")
    best = repeated[0]
    utility = layer.combinator.score_sequence_utility(best)
    print(f"  best: {' > '.join(best.tokens)} (count {best.count}, "
          f"utility {utility})")
    print()

    for purpose in ("memory", "explanation"):
        utterance = layer.utterances.build(stream, purpose=purpose)
        translation = layer.translator.translate_utterance(utterance)
        print(f"proto-utterance ({purpose}):")
        print(f"  {utterance.render()}")
        print(f"  confidence: {utterance.confidence}  grounding refs: "
              f"{len(utterance.grounding_refs)}")
        print(f"  debug translation: {translation}")
        safety = layer.safety.validate_utterance(utterance)
        print(f"  safety: {'ok' if safety.safe else safety.violations}")
        print()
    print("note: a proto-utterance is an internal symbolic sequence "
          "built for a measured purpose; the translation exists only so "
          "humans can inspect it.")


if __name__ == "__main__":
    main()
