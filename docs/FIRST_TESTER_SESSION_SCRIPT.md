# First Tester Session Script

An ordered session script for the first trusted tester. Follow the phases in order. The fixture demo (phase D) comes before any live-read-only step. Live-read-only (phases G-I) is **optional** and governance-gated. Stop conditions appear before every risky phase -- stop conditions override curiosity.


## A. Preparation

- (required) read the release notes (TESTER_RELEASE_NOTES.md)
- (required) read the safety boundaries (TESTER_SAFETY_BOUNDARIES.md)
- (required) read the known issues (TESTER_KNOWN_ISSUES.md)
- (required) confirm you understand this is a local tester RC only -- not a public release and not a product launch
- (required) confirm you will not provide secrets, tokens, credentials, or private data
- (required) confirm you will not interpret any report as evidence of consciousness, life, or agency

> **Stop condition:** STOP if any required doc claims consciousness/life/agency; preserve it and report it.

## B. Install


```bash
python -m venv .venv
```
- (manual) Windows: activate with `.venv\Scripts\Activate.ps1`; Unix/macOS: `source .venv/bin/activate`

```bash
pip install -e .
```

## C. Doctor


```bash
python -m solaris_ai_nn doctor
```

> **Stop condition:** STOP the session if doctor is blocked or its output is unreadable; do not work around a doctor blocker.

## D. Fixture Demo


```bash
python -m solaris_ai_nn tester-demo --state-dir .solaris_ai_nn_tester --profile fixture_tester_v0
```

> **Stop condition:** The fixture demo must succeed before any live-read-only step. STOP the session if it fails without a clear report.

## E. Static Console


```bash
python -m solaris_ai_nn tester-console --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester --console-dir .solaris_ai_nn_tester/console
```
- (manual) open `.solaris_ai_nn_tester/console/INDEX.md` (read-only)
- (manual) optionally open `.solaris_ai_nn_tester/console/INDEX.html` yourself in a browser you open manually

> **Stop condition:** STOP if the console fails to show blockers/warnings or hides quarantine or membrane bypass.

## F. Feedback Init


```bash
python -m solaris_ai_nn tester-feedback-init --tester-state-dir .solaris_ai_nn_tester
```

## G. Optional Live-Read-Only Init


```bash
python -m solaris_ai_nn tester-live-init --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live
```

> **Stop condition:** Live-read-only is OPTIONAL and governance-gated. Review the governance template by hand first. STOP live testing if governance is missing/unclear or the feeder registry allows a forbidden source.

```bash
python -m solaris_ai_nn tester-live-doctor --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live
```

```bash
python -m solaris_ai_nn tester-live-samples --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live
```

## H. Optional Live-Read-Only Sample Validation

- (optional) confirm safe samples are accepted and unsafe samples are quarantined

> **Stop condition:** STOP live testing if an unsafe sample is accepted as safe, or if quarantine fails.

## I. Optional Live-Read-Only Run


```bash
python -m solaris_ai_nn tester-live-run --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live --run-birth --run-membrane --run-integration --run-observation --max-events 500
```

> **Stop condition:** Only after governance is manually reviewed and approved, and only after the fixture demo passed. STOP live testing if the membrane is missing or a raw-event bypass is detected. Solaris never starts feeders.
- (optional) refresh the console after the live run

```bash
python -m solaris_ai_nn tester-console --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester --console-dir .solaris_ai_nn_tester/console
```

## J. Bundle Generation


```bash
python -m solaris_ai_nn tester-feedback-report --tester-state-dir .solaris_ai_nn_tester
```

```bash
python -m solaris_ai_nn tester-feedback-bundle --tester-state-dir .solaris_ai_nn_tester
```

```bash
python -m solaris_ai_nn tester-bundle --state-dir .solaris_ai_nn_tester
```

```bash
python -m solaris_ai_nn tester-live-bundle --state-dir .solaris_ai_nn_live --tester-state-dir .solaris_ai_nn_tester/live
```

## K. Feedback Completion

- (required) complete the feedback forms with install/CLI/report confusion; feedback is local QA evidence, never training. Do not include secrets or private data.

## L. Post-Test Handoff

- (required) review the handoff guide; review each artifact before sharing; send manually only if the developer requests it

> **Stop condition:** STOP and preserve artifacts if any critical stop condition occurred. Never send artifacts anywhere automatically; sharing is manual only.

_Local fixture-first session script. Every command is local and read-only with respect to feeders; none send artifacts anywhere and none create releases/tags/issues. Solaris controls nothing; it is local-only and non-actuating and makes no claim of consciousness/life/agency._