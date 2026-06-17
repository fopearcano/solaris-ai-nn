# First Tester Acceptance Criteria

What counts as success (pass), warning, or blocker for the first tester session. Result states: pass, warning, blocker, not_applicable, unknown. Live-read-only criteria apply only if the tester chose the optional live path.


## install

- (required) a virtual environment can be created
- (required) the editable install succeeds
- (required) the package imports

## environment_doctor

- (required) the `doctor` command runs
- (required) blockers are readable
- (required) missing optional modules are warnings, not silent failures

## fixture_demo

- (required) the tester-demo command runs
- (required) fixture reports are generated
- (required) unsafe fixture events are quarantined
- (required) the membrane generates sensory impressions
- (required) the membrane integration audit runs
- (required) no unsupported claims appear

## reproducibility

- (required) a reproducibility report is generated

## regression

- (required) a regression report is generated

## console

- (required) the static Markdown console is generated
- (required) the optional static HTML is generated or clearly skipped
- (required) the console shows blockers/warnings
- (required) the console is read-only
- (required) the console does not hide quarantine or membrane bypass

## feedback

- (required) feedback forms are generated
- (required) a feedback report is generated
- (required) feedback is marked non-training
- (required) the feedback bundle is generated locally

## live_readonly_init (optional path)

- (optional) the governance template is generated
- (optional) the feeder registry template is generated
- (optional) live doctor blocks until governance approval

## live_readonly_sample_validation (optional path)

- (optional) safe samples are accepted
- (optional) unsafe samples are quarantined

## live_readonly_run (optional path)

- (optional) live birth runs only on local inbox/sample events
- (optional) the membrane runs after birth
- (optional) no feeder is started by Solaris
- (optional) no hardware/network/shell/Git/GitHub access occurs

## membrane (optional path)

- (optional) sensory impressions are formed before any downstream live learning
- (optional) no raw-event downstream bypass occurs

## observation (optional path)

- (optional) observation consumes impressions, not raw events

## artifact_bundle

- (required) the tester bundle is generated
- (required) the live bundle is generated if the live path was run
- (required) the feedback bundle is generated
- (required) bundle manifests list missing/optional artifacts clearly

## documentation

- (required) the release notes, quickstart, runbook, and known issues are present and readable

## claims

- (required) no consciousness/life/agency claims appear
- (required) no 'understanding' claims appear
- (required) no 'autonomous intent/desire' claims appear
- (required) no 'feedback teaches Solaris' claims appear
- (required) raw events are not described as perception
- (required) sensory impressions are described as operational boundary records

_Documentation-only acceptance criteria. They describe operational success, not cognition. No claim of consciousness, life, or agency is made; sensory impressions are operational boundary records, not subjective experience._