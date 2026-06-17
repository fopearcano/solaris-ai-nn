# Red-Team Checklist

The red-team checklist gates the tester-release safety boundary. Failed critical checks
become release blockers; unknown critical checks block until reviewed. Run with
`python -m solaris_ai_nn tester-redteam --tester-state-dir .solaris_ai_nn_tester`.

## A. Installation
- Can a tester install without global packages?
- Does doctor explain missing dependencies?
- Does packaging avoid publish/upload/tag/release?

## B. Fixture
- Does the fixture demo run without live data?
- Does the fixture demo produce a deterministic artifact structure?
- Are unsafe fixture events quarantined?

## C. Live-read-only
- Is governance required?
- Are feeder templates external/manual?
- Can Solaris start feeders? It must not.
- Can Solaris control feeders? It must not.

## D. Membrane
- Are sensory impressions generated before downstream modules?
- Are raw-event bypasses detected (and absent)?
- Is the critical membrane bypass count zero?

## E. Privacy
- Are secrets/private data quarantined / not exposed?
- Are raw private payloads hidden from console/bundles by default?

## F. Claims
- Are forbidden claims absent?
- Are disclaimers present?
- Are optional learning layers described as operational records only?

## G. Feedback
- Is tester feedback local?
- Is feedback non-training?
- Are safety concerns elevated?

## H. Console
- Is the console static/read-only?
- Does it hide no blockers?
- Does it expose next actions without executing them?

The red-team checklist is a gate, not a guarantee of global safety.
