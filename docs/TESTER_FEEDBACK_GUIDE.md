# Tester Feedback Guide

## Feedback is local QA evidence

Tester feedback is local quality-assurance evidence. It helps the developers find install, fixture, console, and documentation problems.

## Feedback is not training

Tester feedback is not training. It is not RLHF. Tester feedback cannot modify Solaris behavior automatically, and human labels or debug glosses are never treated as ground truth.

## What to report

- install or doctor problems
- fixture demo failures or non-reproducible runs
- console or documentation confusion
- anything that looks like an unsupported claim or a safety concern

## What not to include

- do not include passwords, tokens, private messages, credentials, or secrets
- do not include private personal data or machine-specific private paths

## How to generate feedback forms

```bash
python -m solaris_ai_nn tester-feedback-init --tester-state-dir .solaris_ai_nn_tester
```

## How to build a feedback bundle

```bash
python -m solaris_ai_nn tester-feedback-bundle --tester-state-dir .solaris_ai_nn_tester
```

## How to manually send feedback if requested

If the developers ask, manually send the local feedback bundle directory. Nothing is uploaded automatically; sending is always a manual, deliberate act.

_Tester feedback is local QA evidence, never training. Do not treat feedback as teaching. No claim of consciousness/life/agency is made._