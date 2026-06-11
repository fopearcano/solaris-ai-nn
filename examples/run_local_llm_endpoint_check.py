#!/usr/bin/env python3
"""Local LLM endpoint safety check: config only, no model required.

    python examples/run_local_llm_endpoint_check.py \\
        --endpoint-url http://127.0.0.1:11434

Verifies the localhost-only rule against the given URL and prints the
safety decision. Nothing is contacted unless ``--try-request`` is passed,
and even then a dead endpoint just produces a graceful refusal.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.llm_adapter import (
    LLMAdapterConfig,
    LLMAdapterSafetyValidator,
    LLMRequest,
    LLMTaskType,
    LocalHTTPLLMAdapter,
    is_localhost_url,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Local LLM endpoint safety check")
    parser.add_argument("--endpoint-url", type=str,
                        default="http://127.0.0.1:11434")
    parser.add_argument("--provider", type=str,
                        default="ollama_compatible",
                        choices=("ollama_compatible",
                                 "lmstudio_compatible",
                                 "generic_local_http"))
    parser.add_argument("--try-request", action="store_true",
                        help="actually POST one request (graceful "
                             "refusal if nothing is listening)")
    args = parser.parse_args()

    print("=" * 70)
    print("Solaris-AI-NN -- local LLM endpoint safety check (config "
          "only)")
    print("=" * 70)
    print(f"endpoint: {args.endpoint_url}")
    print(f"localhost: {is_localhost_url(args.endpoint_url)}")

    config = LLMAdapterConfig(enabled=True, provider=args.provider,
                              endpoint_url=args.endpoint_url,
                              timeout_s=3.0)
    validator = LLMAdapterSafetyValidator()
    report = validator.validate_endpoint(config)
    print(f"safety decision: {'ALLOWED' if report.safe else 'REFUSED'}")
    for violation in report.violations:
        print(f"  - {violation}")

    if args.try_request and report.safe:
        adapter = LocalHTTPLLMAdapter(config=config)
        response = adapter.generate(LLMRequest(
            task_type=LLMTaskType.PARAPHRASE_RESPONSE,
            input_text="Status summary: steps=1.",
            allowed_facts=["Status summary: steps=1."]))
        if response.refused:
            print(f"request outcome: refused gracefully "
                  f"({response.refusal_reason[:80]})")
        else:
            print(f"request outcome: ok "
                  f"({len(response.output_text)} chars from "
                  f"{response.raw_model_name})")
    elif args.try_request:
        print("request skipped: the endpoint failed the safety check")
    else:
        print("no request attempted (config check only); pass "
              "--try-request to POST once")
    print()
    print("note: remote endpoints are refused by default; only "
          "localhost is permitted, and a missing local model is a "
          "graceful refusal, never an error.")


if __name__ == "__main__":
    main()
