# First Tester Protocol

The First Tester Protocol (Prompt 81) is the final operational layer before the first
human tester touches the release candidate. It is a local, documentation-only layer: it
generates a session script, task sheet, acceptance criteria, stop conditions, artifact
handoff guide, and post-test review template. It does not run the tester session.

## What it is

A precise, ordered protocol so the first trusted tester knows exactly what to install,
what to run, in what order, what files to inspect, what counts as success/warning/blocker,
when to stop, what feedback to record, what artifacts to preserve, what not to share, and
how to hand off artifacts to the developer.

## What it is not

- not a public release and not a product launch
- not a consciousness demo
- it does not run the tester session automatically
- it does not publish/upload, create GitHub issues/releases/tags, or upload packages
- Solaris never starts feeders and never controls hardware
- Solaris does not access network/shell/Git/GitHub/browser/OS
- tester feedback is not training and is never treated as ground truth

## Order of operations

The fixture demo comes first. Live-read-only is **optional** and governance-gated:
external feeders are manual, and Solaris never starts or controls them. The environmental
membrane is required before any downstream live learning -- raw events are audit material,
not perception, and sensory impressions are operational boundary records, not subjective
experience.

## How it is generated

```bash
python -m solaris_ai_nn first-tester-protocol --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn first-tester-script --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn first-tester-acceptance --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn first-tester-stops --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn first-tester-handoff --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn first-tester-review --tester-state-dir .solaris_ai_nn_tester
```

If the RC, packaging doctor, or safety freeze is blocked, the protocol still generates the
docs but marks the session as blocked. Stop conditions override curiosity; reports are not
evidence of consciousness, life, or agency.

See `FIRST_TESTER_SESSION_SCRIPT.md`, `FIRST_TESTER_ACCEPTANCE_CRITERIA.md`,
`FIRST_TESTER_STOP_CONDITIONS.md`, `FIRST_TESTER_HANDOFF.md`, and
`FIRST_TESTER_POST_TEST_REVIEW.md`.
