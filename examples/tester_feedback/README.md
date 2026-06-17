# Tester feedback examples (Prompt 77)

The **Tester Feedback** system is a local QA ledger. A tester records install/CLI/
fixture/live problems, membrane/quarantine confusion, safety concerns, documentation/
console confusion, unsupported-claim concerns, performance issues, missing/unexpected
artifacts, feeder/governance issues, and suggestions.

> **This is not the Human Feedback / Teaching Loop and not RLHF.** Feedback is **local**,
> structured, append-only QA evidence. It is **never** training data, **never** ground
> truth, **never** a command, and it **never** automatically modifies Solaris behaviour,
> creates GitHub issues, or uploads anything. Release blockers and safety concerns are
> **developer review items**.

## Sample feedback files

- `sample_bug_report.json` — a fixture-demo bug report.
- `sample_safety_concern.json` — a feeder-control-risk safety concern (release blocker).
- `sample_confusion_report.json` — a fixture-vs-live confusion report.
- `sample_suggestion.json` — a documentation suggestion.
- `sample_release_blocker_feedback.json` — a consciousness-claim concern (stop-testing).

## Try it

```bash
python -m solaris_ai_nn tester-feedback-init --tester-state-dir .solaris_ai_nn_tester
# Edit a feedback form / copy a sample, then ingest it (local only):
python -m solaris_ai_nn tester-feedback-ingest --tester-state-dir .solaris_ai_nn_tester --ingest-path examples/tester_feedback/sample_bug_report.json
python -m solaris_ai_nn tester-feedback-report --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-feedback-blockers --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-feedback-bundle --tester-state-dir .solaris_ai_nn_tester
```

Do **not** include secrets, credentials, API keys, tokens, private messages, or raw
private payloads in feedback. Artifact references must be local paths only. Nothing in
this system implies consciousness, sentience, biological life, personhood, agency, free
will, emotion, feeling, understanding, self-awareness, autonomous self-improvement, or
subjective experience.
