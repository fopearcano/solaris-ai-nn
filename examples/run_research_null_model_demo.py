#!/usr/bin/env python3
"""Research null-model demo: could the "growth" be noise or accumulation?

    python examples/run_research_null_model_demo.py --state-dir .solaris_ai_nn_research/test_null_model

Runs a static no-learning model and a shuffled-symbol-label null model. The
static model produces zero change; the shuffle model returns inconclusive when
the sample is too small. Null models are cautious by design and never overstate
statistical certainty.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_lab import NullModel, NullModelType


def main():
    parser = argparse.ArgumentParser(description="Research null-model demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_research/test_null_model")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    static = NullModel(NullModelType.STATIC_NO_LEARNING_MODEL).evaluate(
        [0.2, 0.2, 0.2, 0.2])
    small = NullModel(NullModelType.SYMBOL_LABEL_SHUFFLE).evaluate([1, 2, 3])
    big = NullModel(NullModelType.SYMBOL_LABEL_SHUFFLE).evaluate(
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 1.2, 1.6])

    out = {"static": static.to_dict(), "small_sample": small.to_dict(),
           "larger_sample": big.to_dict()}
    path = os.path.join(args.state_dir, "null_models.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)

    print("=== Research null-model demo ===")
    print(f"static no-learning change distinguishable : "
          f"{static.distinguishable_from_null} (zero change expected)")
    print(f"small-sample shuffle inconclusive         : {small.inconclusive}")
    print(f"larger-sample shuffle distinguishable      : "
          f"{big.distinguishable_from_null} "
          f"(obs={big.observed_value}, null_mean={big.null_mean})")
    print(f"written                                   : {path}")
    print("note : null models are weak, cautious estimates, not significance "
          "tests; small samples are inconclusive.")


if __name__ == "__main__":
    main()
