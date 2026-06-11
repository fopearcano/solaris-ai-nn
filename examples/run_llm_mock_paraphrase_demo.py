#!/usr/bin/env python3
"""Mock LLM paraphrase demo: readability changes, truth does not.

    python examples/run_llm_mock_paraphrase_demo.py

The deterministic response is shown beside its mock-LLM paraphrase, with
the grounding and ClaimGuard verdicts, then an unsafe adapter is forced
and the pipeline falls back to the deterministic original. No real model
endpoint is involved anywhere.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.communication.gateway import CommunicationGateway
from solaris_ai_nn.governance.policy import GovernancePolicy
from solaris_ai_nn.llm_adapter import LLMParaphraser, MockLLMAdapter
from solaris_ai_nn.llm_adapter.audit import LLMAuditLog


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mock LLM paraphrase demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/llm_mock")
    args = parser.parse_args()

    print("=" * 70)
    print("Solaris-AI-NN -- mock LLM paraphrase demo (translator, not "
          "authority)")
    print("=" * 70)

    gateway = CommunicationGateway(
        state_dir=args.state_dir,
        components={"governance": GovernancePolicy(),
                    "ops_status": {"steps": 120, "health_level": "ok",
                                   "mode": "demo"}})
    deterministic = gateway.handle_input("status")
    print("deterministic response:")
    print(f"  {deterministic.text}")
    print()

    llm_gateway = CommunicationGateway(
        state_dir=args.state_dir + "/llm", enable_llm_adapter=True,
        components={"governance": GovernancePolicy(),
                    "ops_status": {"steps": 120, "health_level": "ok",
                                   "mode": "demo"}})
    paraphrased = llm_gateway.handle_input("status")
    print("paraphrased response (mock adapter):")
    print(f"  {paraphrased.text}")
    print(f"  llm_paraphrased: "
          f"{paraphrased.metadata.get('llm_paraphrased', False)}")
    snap = llm_gateway.llm_paraphraser.snapshot()
    print(f"  grounding: validations="
          f"{snap['grounding']['validations_run']} failures="
          f"{snap['grounding']['failures_total']}")
    print(f"  claim guard: post-scan failures="
          f"{snap['claim_filter']['post_scan_failures']}")
    print()

    print("forced-unsafe adapter (output invents consciousness claims):")
    audit = LLMAuditLog(state_dir=Path(args.state_dir) / "llm")
    bad = LLMParaphraser(adapter=MockLLMAdapter(force_unsafe_output=True),
                         audit=audit)
    response = gateway.handle_input("status")
    before = response.text
    after = bad.paraphrase_response(response)
    print(f"  fallback to deterministic: {after.text == before}")
    print(f"  rejected paraphrases: {bad.rejected_count}  "
          f"fallbacks: {bad.fallback_count}")
    print(f"  audit log: {audit.path} ({audit.rows_written} row(s), "
          f"hashes only)")
    print()
    print("note: the LLM changes wording only; grounding validation and "
          "ClaimGuard gate every output, and the deterministic text is "
          "always the fallback.")


if __name__ == "__main__":
    main()
