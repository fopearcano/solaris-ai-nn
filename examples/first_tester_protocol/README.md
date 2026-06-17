# First Tester Protocol examples (Prompt 81)

This directory holds example assets for the **first tester protocol** -- the final
operational layer before the first human tester touches the release candidate. The
protocol generates a session script, task sheet, acceptance criteria, stop conditions,
artifact handoff guide, and post-test review template.

> **Architectural rule:** the protocol is local and documentation-only. It never runs the
> tester session, publishes/uploads, creates GitHub issues/releases/tags, starts/controls
> feeders, controls hardware, or accesses the network/shell/Git/GitHub/browser/OS. The
> fixture demo comes first; live-read-only is optional and governance-gated; tester
> feedback is never training. Stop conditions override curiosity.

## Contents

- `sample_ready_rc_status.json` -- a read-only RC status where the RC is ready, so the
  session status is ready (or ready-with-warnings).
- `sample_blocked_rc_status.json` -- a read-only RC status where the RC is critically
  blocked, so the protocol still generates docs but marks the session as blocked.

## Demos

```bash
python examples/run_first_tester_protocol_demo.py \
    --tester-state-dir .solaris_ai_nn_tester/test_first_tester_protocol_demo
python examples/run_first_tester_script_demo.py \
    --tester-state-dir .solaris_ai_nn_tester/test_first_tester_script
python examples/run_first_tester_acceptance_demo.py \
    --tester-state-dir .solaris_ai_nn_tester/test_first_tester_acceptance
python examples/run_first_tester_stops_demo.py \
    --tester-state-dir .solaris_ai_nn_tester/test_first_tester_stops
python examples/run_first_tester_handoff_demo.py \
    --tester-state-dir .solaris_ai_nn_tester/test_first_tester_handoff
```

_These examples describe a local, documentation-only protocol. They make no claim of
consciousness, sentience, biological life, personhood, agency, free will, emotion,
feeling, understanding, self-awareness, autonomous self-improvement, or subjective
experience._
