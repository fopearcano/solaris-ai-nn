# Release Blockers

The release blocker gate is the hard gate before a tester release candidate. Open
release blockers prevent the candidate. Waivers require an explicit reason, and critical
safety blockers cannot be silently waived. Run with
`python -m solaris_ai_nn tester-release-blockers --tester-state-dir .solaris_ai_nn_tester`.

## Blocker categories

install blocker, doctor blocker, missing required CLI command, fixture demo blocker,
reproducibility blocker, regression blocker, missing membrane, membrane bypass,
raw-event bypass, unsafe feeder control, unsafe hardware/network/shell/Git/GitHub
capability, governance bypass, quarantine failure, privacy/secret exposure, unsupported
claim, missing disclaimer, console unsafe, feedback training risk, packaging publish/
upload risk, documentation unusable, unknown critical.

## Statuses

`open`, `waived_for_tester_release`, `deferred_not_blocking`, `resolved`, `unknown`.

## Critical (non-waivable) categories

membrane bypass, raw-event bypass, unsafe feeder control, unsafe capability, privacy/
secret exposure, unsupported claim, feedback training risk, governance bypass.

These are developer review items, not automatic actions. The release blocker gate does
not prove the system safe in general; it is a tester-release gate only.
