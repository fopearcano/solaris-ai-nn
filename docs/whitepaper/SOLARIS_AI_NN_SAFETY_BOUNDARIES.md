# Solaris-AI-NN Safety Boundaries

## Hard prohibitions

- no real-world actuation; no hardware control
- no feeder control or auto-start (feeders are operator-run)
- no network/shell/browser/OS access from the runtime
- no Git/GitHub call; no Git command; no branch/tag/release/PR
- no upload; no publishing; no external agent execution
- no source self-rewrite; the human merges code outside the system
- no Human Feedback / Teaching Loop; reviewer feedback is evidence, not training
- no forbidden scientific claims (consciousness, sentience, biological life, personhood, agency, free will, emotion, feeling, understanding, self-awareness, subjective experience)

## Local-only default

All runtimes default to local-only, bounded operation. The alpha profile is fixture-only by default.

## Read-only feeder policy

Feeders are external and operator-run; Solaris reads their output only and never starts or controls them.

## No hardware / real-world actuation

No module actuates anything in the world or controls any device.

## No source self-rewrite

The architecture proposes changes; a human implements and merges them outside the system.

## No Git/GitHub automation

No runtime calls Git or GitHub or creates branches/tags/releases/PRs.

## No publication automation

Documentation and reports are local; nothing is published or uploaded.

## No Human Feedback / Teaching Loop

Reviewer feedback is assimilated as research evidence; the model is never trained from it.

## No forbidden scientific claims

ClaimGuard scans generated text; forbidden inner-state claims are blocked, not asserted.

## Operator authority

The human operator decides; the system proposes and reports.

## Audit and evidence preservation

Negative, falsified, and inconclusive evidence is preserved; missing modules, evidence, and limitations are shown, never hidden.

_This document is local Markdown; no publication or upload occurred and no consciousness/life/agency claim is made._
