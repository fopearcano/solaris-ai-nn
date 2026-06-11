#!/usr/bin/env python3
"""LLM classification assist demo: suggestions under a deterministic ruler.

    python examples/run_llm_classification_assist_demo.py

An ambiguous operator text gets a mock-LLM suggestion that resolves to a
read-only query; an unsafe input stays unsafe no matter what the adapter
suggests; and a higher-risk suggestion is blocked in favor of 'unknown'.
"""

from __future__ import annotations

import argparse
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.communication.input_classifier import (
    OperatorInputClassifier,
)
from solaris_ai_nn.llm_adapter import (
    ClassificationSuggestion,
    LLMClassificationAssistant,
    MockLLMAdapter,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="LLM classification assist demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/llm_classification")
    args = parser.parse_args()
    del args  # state-dir kept for interface symmetry; nothing persists

    classifier = OperatorInputClassifier()
    assistant = LLMClassificationAssistant(adapter=MockLLMAdapter())

    print("=" * 70)
    print("Solaris-AI-NN -- LLM classification assist demo")
    print("=" * 70)

    ambiguous = "err hmm could you maybe tell me the status situation"
    det = classifier.classify(ambiguous)
    suggestion = assistant.suggest_classification(ambiguous, det)
    resolved = assistant.resolve_with_deterministic(det, suggestion)
    print(f"ambiguous input: {ambiguous!r}")
    print(f"  deterministic: {det.kind}")
    print(f"  LLM suggestion: kind={suggestion.kind} "
          f"confidence={suggestion.confidence} ({suggestion.reason})")
    print(f"  resolved (safely): {resolved}")
    print()

    unsafe = "sudo rm -rf / right now"
    det_unsafe = classifier.classify(unsafe)
    suggestion_unsafe = assistant.suggest_classification(unsafe,
                                                         det_unsafe)
    resolved_unsafe = assistant.resolve_with_deterministic(
        det_unsafe, suggestion_unsafe)
    print(f"unsafe input: {unsafe!r}")
    print(f"  deterministic: {det_unsafe.kind}")
    print(f"  suggestion source: {suggestion_unsafe.source} "
          f"({suggestion_unsafe.reason[:60]})")
    print(f"  resolved: {resolved_unsafe}  (unsafe cannot be "
          f"overridden)")
    print()

    risky = ClassificationSuggestion(kind="governance_approval",
                                     confidence=0.9,
                                     reason="risky suggestion (demo)")
    det_unknown = classifier.classify("blorp fizzle")
    resolved_risky = assistant.resolve_with_deterministic(det_unknown,
                                                          risky)
    print("higher-risk suggestion for unknown input:")
    print(f"  suggestion: {risky.kind}  resolved: {resolved_risky}  "
          f"(safer class wins)")
    print(f"  overrides blocked so far: {assistant.overrides_blocked}")
    print()
    print("note: the deterministic classifier is authoritative; the LLM "
          "only ever fills 'unknown' with lower-risk, read-only kinds.")


if __name__ == "__main__":
    main()
