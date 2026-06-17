# Tester Runbook

An ordered, fixture-first runbook for the local tester release candidate. Follow the sections in order; the fixture path comes first and live-read-only is optional and governance-gated.

## A. Install

```bash
python -m venv .venv
pip install -e .
python -m solaris_ai_nn doctor
```

> Use a virtual environment. A global install is not supported and admin/root is never required.

## B. Fixture run (do this first)

```bash
python -m solaris_ai_nn tester-demo --state-dir .solaris_ai_nn_tester --profile fixture_tester_v0
python -m solaris_ai_nn tester-console --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester --console-dir .solaris_ai_nn_tester/console
```

> The fixture demo is self-contained. Do not run external feeders before the fixture path passes.

## C. Inspect console

- open `.solaris_ai_nn_tester/console/INDEX.md`
- optionally open `.solaris_ai_nn_tester/console/INDEX.html` manually in a browser you open yourself

> The console is read-only. It controls no feeders, hardware, or network.

## D. Live-read-only init (optional, governance-gated)

```bash
python -m solaris_ai_nn tester-live-init --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live
python -m solaris_ai_nn tester-live-doctor --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live
python -m solaris_ai_nn tester-live-samples --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live
```

> Read the governance template before enabling live-read-only. External feeders are manual and run by you, never started by Solaris.

## E. Optional live-read-only run

```bash
python -m solaris_ai_nn tester-live-run --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live --run-birth --run-membrane --run-integration --run-observation --max-events 500
```

> Only after the fixture path passes and governance is read. The membrane forms impressions before any downstream live learning; raw events are audit material, not perception.

## F. Feedback

```bash
python -m solaris_ai_nn tester-feedback-init --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-feedback-report --tester-state-dir .solaris_ai_nn_tester
python -m solaris_ai_nn tester-feedback-bundle --tester-state-dir .solaris_ai_nn_tester
```

> Feedback is local QA evidence, never training. Do not include passwords, tokens, private messages, credentials, or secrets.

## G. Stop conditions

- doctor is blocked
- the fixture demo fails
- the safety freeze reports a blocker
- governance is unclear
- a forbidden source appears
- the feeder registry looks unsafe
- the membrane is missing when live modules ran
- a raw-event bypass is detected
- an unsupported claim appears
- private data or a secret appears
- you are unsure what a command does

> If any stop condition occurs, stop and report it via local feedback. Do not work around a safety blocker.

_Local fixture-first runbook. Every command is local and read-only with respect to feeders; nothing is sent anywhere and no release/tag/issue is created. The runtime is local-only and non-actuating and makes no claim of consciousness/life/agency._