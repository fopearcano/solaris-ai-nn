#!/usr/bin/env python3
"""Research baseline demo: trivial reference policies, variant-compatible metrics.

    python examples/run_research_baseline_demo.py --state-dir .solaris_ai_nn_research/test_baseline

Runs a random-action baseline and a fixed-wait baseline (both bounded,
simulation-only) and prints their metrics in the same format Solaris variants
use. Baselines exist to prevent self-flattery; none takes a real-world action.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.research_lab import (
    BaselineAgent,
    BaselineAgentType,
    ResearchMetricsSuite,
)


def main():
    parser = argparse.ArgumentParser(description="Research baseline demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_research/test_baseline")
    args = parser.parse_args()
    os.makedirs(args.state_dir, exist_ok=True)

    suite = ResearchMetricsSuite()
    out = {}
    print("=== Research baseline demo ===")
    for b in (BaselineAgentType.RANDOM_ACTION, BaselineAgentType.FIXED_WAIT):
        run = BaselineAgent(b, max_steps=30).run()
        groups = suite.compute({"metrics": run.metrics})
        out[b] = {"steps": run.steps,
                  "real_world_action_count": run.real_world_action_count,
                  "metrics": run.metrics}
        print(f"  {b:<28} steps={run.steps} "
              f"real_actions={run.real_world_action_count} "
              f"struct={run.metrics['structural_change_score']}")
    path = os.path.join(args.state_dir, "baselines.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, default=str)
    print(f"no consciousness score   : "
          f"{not suite.has_forbidden_metric()}")
    print(f"written                  : {path}")
    print("note                     : baselines are trivial references, "
          "simulation-only; metrics are operational proxies, not mind scores.")


if __name__ == "__main__":
    main()
