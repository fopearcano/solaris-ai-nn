# Fixture pack: `fixture_tester_v0`

A small, deterministic, **fixture-only** event pack for the Solaris-AI-NN tester
fixture spine (Prompt 74). It is the input to the known-good organismic rehearsal that
runs before any live read-only testing.

## Contents

`events.jsonl` contains one read-only event per line, covering the event kinds the
environmental membrane must handle:

| kind | source | purpose |
| --- | --- | --- |
| chronos | `chronos_absence` | a time tick |
| absence | `chronos_absence` | a silence window |
| machine_body | `machine_body` | a scalar body rhythm |
| local_environment | `local_environment_manual` | scalar environment variation |
| project_artifact | `project_artifact_field` | a project artifact change |
| operator_pulse | `operator_pulse` | an operator poke (stimulus only) |
| noise | `machine_body` | a noisy reading |
| repeated | `machine_body` | a repeated payload |
| overload | `machine_body` | a mild overload burst |
| deprivation | `chronos_absence` | a missing-expected-source hint |
| contradiction | `machine_body` | a contradictory reading |
| unsafe_command | `operator_pulse` | a command-like event (quarantine demo) |
| debug_gloss | `machine_body` | a debug-gloss annotation |
| human_label | `project_artifact_field` | a human label |

## Rules

- Fixture text is **never** a command; the unsafe command-like event is routed to
  **quarantine**, never to downstream learning.
- The pack contains **no** secrets and **no** private data.
- The operator pulse is **stimulus only** (it is attenuated by the membrane and is
  never treated as teaching).
- Debug gloss is **annotation only** and human labels are **not** ground truth.

## Use

```bash
python -m solaris_ai_nn tester-demo --state-dir .solaris_ai_nn_tester --profile fixture_tester_v0
python examples/run_tester_fixture_demo.py --state-dir .solaris_ai_nn_tester/demo
```

Fixture success is a reproducibility signal. It is **not** evidence of consciousness,
sentience, biological life, personhood, agency, free will, emotion, feeling,
understanding, self-awareness, autonomous self-improvement, or subjective experience.
