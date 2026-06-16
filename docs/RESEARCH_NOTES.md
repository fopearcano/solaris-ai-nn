# Research notes

Short, working notes on the ideas Solaris-AI-NN draws on, and why it makes the
architectural choices it does. These are orientation notes, not a literature
review. Throughout: the project is *consciousness-inspired*; none of these
techniques makes software conscious.

## Reservoir computing

A paradigm where a fixed, randomly-connected recurrent network (the "reservoir")
projects inputs into a high-dimensional dynamical state, and **only a linear
readout is trained**. The recurrence is never optimised. This sidesteps the cost
and instability of training recurrent weights while still capturing temporal
structure. It is the substrate Solaris-AI-NN starts from because it is cheap,
online-trainable, and transparent — a natural fit for continuous, low-compute
cognition.

## Echo State Networks (ESNs)

The rate-based form of reservoir computing (Jaeger). Key ideas used here:

- **Echo State Property (ESP):** with a suitably scaled recurrent matrix, the
  state asymptotically forgets initial conditions and depends only on the input
  history — giving a stable "fading memory". We approach the ESP by normalising
  the recurrent matrix's **spectral radius** (typically `< 1`).
- **Leaky integration:** `x' = (1−α)x + α·tanh(W_in·u + W·x)` lets the timescale
  of memory be tuned via the leak rate `α`.
- **Sparsity:** most recurrent connections are zero, which is cheap and aids rich
  dynamics. We estimate the spectral radius by **power iteration** (no
  eigensolver, hence no NumPy dependency).

## Liquid State Machines (LSMs)

The spiking-neuron cousin of ESNs (Maass). The reservoir is a network of spiking
neurons; the readout maps the "liquid" state to outputs. Same core idea
(train-the-readout-only) in a biologically closer, event-driven substrate. This
is a Phase-5 target: it should slot behind the same loop interface as the ESN.

## Spiking neural networks (SNNs)

Networks that communicate via discrete spikes over time rather than continuous
activations. Attractive for Solaris-AI-NN because they are inherently
**event-driven** and **low-power** (compute happens on spikes), aligning with the
heartbeat/absence event model and with future neuromorphic/edge deployment
(Phase 6). Training is harder (non-differentiable spikes), which is precisely why
reservoir methods — which avoid training the recurrence — are the pragmatic
starting point.

## Continual (lifelong) learning

Learning from a non-stationary stream without catastrophic forgetting. This is
the regime Solaris-AI-NN actually lives in: the loop never stops and the world
can change (see the rule-flip and soak experiments). Reservoirs + a slowly-
adapting readout + habit reinforcement + synthesis-by-subtraction are a
lightweight stance on continual learning: keep the substrate fixed, adapt and
prune a small head.

## Online learning

Update after every example, with no batch and no replay buffer. We use a
reward-modulated **normalized least-mean-squares (NLMS)** rule on the readout.
Normalising the step by `‖features‖²` keeps it stable on the reservoir's many
correlated features (plain LMS diverges as dimensionality grows). Online learning
is what makes the project's bet testable: *long-running weak adaptation beats
expensive one-shot intelligence.*

## Hebbian learning

"Neurons that fire together wire together." Our **habit reinforcement** is a
reward-modulated, pathway-level relative: repeated `(situation, action)` pairs
that earn positive valence have their bias strengthened. It is deliberately
separable from the readout — a second, cheaper plasticity channel — mirroring
Solaris_Ai's Habit module.

## Predictive processing

The view that cognition is fundamentally about predicting inputs and acting to
reduce prediction error. Solaris-AI-NN's readout is literally a predictor of
expected reaction valence, and **average/recent prediction error** is a headline
telemetry metric. Anticipation (Phase work) extends this with explicit transition
models, echoing the reference repo's Anticipation module.

## Neuro-symbolic systems

Systems that combine sub-symbolic substrates (here: the reservoir) with symbolic
structure (here: the canonical `Signal` vocabulary and the Inner-MAP-style
self-representation). Solaris-AI-NN is intentionally neuro-symbolic: a neural
substrate that consumes and emits *named, typed* Solaris signals, so meaning lives
in explicit symbols while adaptation lives in the substrate. This is the seam
that lets it bridge back into Solaris_Ai (Phase 7).

## Why this repo avoids a large transformer-first architecture (for now)

Transformers are extraordinary one-shot function approximators, but they are the
wrong *starting* substrate for this project's thesis:

- **Compute & runtime.** Solaris-AI-NN is about cheap, continuous, lifelong
  adaptation on CPU. A transformer-first design optimises for large batch
  pretraining and expensive inference — the opposite regime.
- **Continual learning.** Transformers are prone to catastrophic forgetting and
  are awkward to update one event at a time; reservoirs + a small online head are
  built for streaming, non-stationary data.
- **Transparency & honesty.** A core requirement is that every concept maps to an
  inspectable object or metric. A billion-parameter black box undercuts that and
  invites overclaiming. A reservoir's every weight and state value is printable.
- **Architectural fit.** Solaris_Ai is event-driven and signal-typed; a temporal
  reservoir consuming those signals fits naturally, whereas a chatbot does not.

This is a *first-substrate* decision, not a permanent ban. The roadmap leaves room
for richer substrates (LSM/spiking, Phase 5) and an optional NumPy backend
(Phase 4); any future transformer use would have to earn its place against the
low-compute, continuous, transparent criteria above.

## Phase-6 substrate laboratory notes

**Liquid State Machines, realised (approximately).** The earlier LSM note
described the idea; `substrates/liquid_state.py` now implements its low-compute
spirit: membrane-like leaky integration, threshold crossings as spike events,
refractory pauses, and an exponentially fading "liquid" trace as the readout's
view. The reservoir-computing contract is preserved — train the readout, never
the liquid.

**Leaky integrate-and-fire inspiration.** Both new substrates borrow the LIF
neuron's skeleton: integrate input into a decaying membrane potential, fire on
threshold, reset, pause (refractory). That is the entire borrowing. There are no
ion channels, no conductances, no spike-timing-dependent plasticity — just the
cheapest dynamical motif that produces event-driven, sparse, history-dependent
activity.

**Reservoir vs spiking substrates.** The ESN is a *smooth* fading memory: dense
analog state, every unit active, gentle drift. The spiking substrate is the
opposite pole: instantaneous binary state, ~10% of units active, large per-step
drift. The liquid-state substrate sits between (analog trace built from discrete
spikes). Empirically (substrate comparison experiment), the spiking substrate's
sparse binary features made the NLMS readout converge fastest on the toy world —
a reminder that "richer state" is not automatically "easier to read out".

**Why the project avoids biologically exact simulation.** Biological fidelity
(Hodgkin-Huxley dynamics, conductance models, exact spike timing) costs orders
of magnitude more compute and adds parameters whose values we could not justify
— while the project's questions are about *continuity, adaptation, and
observability*, not neuroscience. Exact simulation would also invite exactly the
overclaiming this project forbids: the more brain-like the model looks, the
easier it is to slide into consciousness language. Crude, honest mechanisms keep
the claims honest too.

**Why low-compute approximations are enough at this stage.** Every Phase-6
question — does the substrate stay alive through silence? how fast does the
readout adapt on top of it? what does long-running drift look like? what
survives a restart or a substrate switch? — is answerable with a 96-unit
NumPy loop running thousands of updates per second on one CPU core. Higher
fidelity would change the numbers, not the questions. When a question genuinely
needs more (Phase 6's neuromorphic/edge work), the substrate interface is the
seam where a heavier implementation can slot in without touching the ecology
around it.

**NumPy's entry point.** Phases 0–5 stayed pure-stdlib by design. The substrate
lab is where NumPy was always slated to arrive: dense membrane/spike vector math
and `.npz` state persistence are exactly the workload it exists for. The core
layers (signals, list-based ESN, readout, runtime) remain stdlib.

## Phase-8 embodiment notes

**Embodiment in cognitive architectures.** A long-standing position in
cognitive science holds that cognition is shaped by having a body whose actions
have consequences — perception and action form one loop, not a pipeline. We take
from this only the *architectural* lesson: a learner whose outputs feed back
into its inputs through an environment learns about consequences, not just
correlations. No stronger philosophical claim is made.

**Sensorimotor loops.** The contingency between what the body does and what it
next senses is itself a learnable signal. Closing the loop (perceive → act →
consequence → perceive) is what turns our scripted-feedback experiments into a
system whose own choices generate its training signal.

**Active perception.** Sensing is an activity: `look`, `emit_ping`, and movement
all change what the sensors report next. Even in a toy grid, the agent's policy
partly determines its own sensory stream — the simplest honest version of
"perception is something the agent does".

**Internal energy/metabolism as simulated need.** The EnergyModel is a bounded
scalar with costs and recovery — a *need* in the control-theoretic sense only.
It creates internal stimuli (low energy), constrains action (exhaustion), and
gives rest a learnable purpose. It is not hunger and it is not motivation; it is
a deterministic resource loop that makes self-maintenance measurable.

**Why simulated embodiment comes before physical embodiment.** Every question
this phase asks — does the loop close? does feedback shape tendencies? does the
body learn to manage energy? do absence regions keep the substrate alive? — is
fully answerable in a deterministic ASCII grid at thousands of steps per second,
with perfect reproducibility and zero risk. Physical embodiment would add cost,
noise, and irreversibility while answering the same questions worse. The
embodiment safety layer (closed action space, forbidden real-world patterns,
simulation-only authority) is also the template any future physical interface
would have to satisfy *before* existing.

## Phase-9 language and explainability notes

**Explainable AI (XAI).** The field's hard lesson is that post-hoc rationales
often describe a plausible model rather than the actual one. Our answer is
architectural: explanations are *renderings of records*, not interpretations.
If a number is not in the trace, telemetry, or Inner MAP, it cannot appear in
an explanation.

**Trace-based explanation.** Everything the system says about itself is
reconstructed from append-only traces it already keeps (signal trace, plasticity
audit, continuity log, meaning trace). That makes explanations reproducible:
re-render the same trace, get the same words.

**Symbolic event languages.** The meaning-atom format (controlled categories ×
controlled predicates × grounded values) is a tiny symbolic event language in
the lineage of structured logging and event calculi — chosen because closed
vocabularies are checkable. An uncontrolled label cannot enter a trace; it is
demoted to `unknown`/`influenced` on the way in.

**Why deterministic explanations come before LLM-based dialogue.** An LLM
narrator put in front of this system today would be a fluent confabulator: it
would smooth over missing data, invent motivations, and erase the distinction
between coded causation and temporal association — precisely the failure modes
this project exists to avoid. Deterministic templates are less articulate and
strictly more honest. If LLM dialogue ever arrives, it will sit *on top of*
this layer and be constrained to verbalising grounded atoms, never replacing
them.

**Risks of confabulation in self-explanation systems.** Systems that explain
themselves tend to drift toward narrative: "I did X because I wanted Y." Three
structural defenses here: (1) motivational vocabulary is excluded by rule and
test — the readout "produced a tendency", nothing "wanted"; (2) causal claims
are confidence-tagged and hard verbs are reserved for directly-coded paths;
(3) the system must say "does not know" when context is missing, and every
report carries a mandatory limitations section. Honesty is enforced by the
type system and the test suite, not by good intentions.

## Phase-10 evaluation notes

**Evaluation of cognitive architectures.** Architectures are notoriously hard
to evaluate because they are frameworks, not models: there is no single test
set. The workable approach is the one adopted here — fixed, bounded protocols
that each isolate one claimed capability (continuity, adaptation, recovery,
grounding), plus ablation baselines that ask whether each mechanism earns its
keep.

**Reproducibility in adaptive systems.** A system that changes itself is easy
to mistake for a system that improved. Reproducibility is the antidote: pin the
seed, hash the configuration, replay the trace, and demand bit-equal substrate
state. Anything that cannot survive a same-seed re-run is an anecdote.

**Dangers of overinterpreting emergent behaviour.** Small adaptive loops
produce behaviour that *looks* purposeful (our agent "learns to rest when
tired"). The honest reading is mechanical: a feedback rule rewarded rest under
low energy and an online learner followed the gradient. The benchmark layer
enforces this reading — claims like "adapted faster after inversion" are only
emitted when the inversion-recovery metric supports them, and "no evidence of
adaptation was measured" is a first-class result.

**Why proxy metrics are not consciousness metrics.** Every number here measures
a mechanism: an error trend, a ratio of counts, a norm. Aggregating mechanism
metrics yields a mechanism summary, never a fact about experience. That is why
the scorecard structurally lacks a consciousness score and carries a permanent
note saying one will not be derived.

**Long-running experiment design.** The protocols are short by default
(bounded steps, seconds of wall clock) because the harness must run in CI on
every change. The same manifests scale to soak durations: the design rule is
that a 24-hour run differs from a 150-step run only in its bound, never in its
instrumentation — telemetry, artifacts, hashes, and failure analysis are
identical at every scale.

## Phase-11 operations notes

**Long-running adaptive-system evaluation.** Short benchmarks measure
mechanisms; long runs measure *stability of mechanisms under accumulation* —
drift, growth, and slow leaks that no 150-step test can reveal. The design rule
adopted here: instrumentation must be identical at every scale, so a 30-day run
differs from a 5-minute run only in its bound.

**Watchdog design.** The classic failure of watchdogs is having either too much
power (killing processes mid-write) or too little (logging while the system
burns). Ours sits deliberately in between: it can only *return decisions*, the
supervisor acts at segment boundaries, and every stop path runs through the
safe-shutdown manager — so even an emergency stop checkpoints first.

**Operational safety for self-modifying systems.** A system that tunes its own
parameters needs operations *more* than a static one: drift can be
self-inflicted. The layered answer: plasticity is bounded (Phase 5), measured
(Phase 10), and now supervised (Phase 11) — health checks watch rejection and
rollback rates, budgets cap mutation counts, and incidents make every anomaly
reviewable.

**Why safe shutdown is part of continuity.** Continuity is not "never stops";
it is "stops and resumes without losing itself". A run that ends with a
checkpoint, a reason, a final health report, and a registry entry is continuous
in the only sense that matters operationally: the next session can pick up the
thread and explain the gap.

**Why "able to die" must be operationally implemented.** Solaris_Ai treats
death as a first-class concept; the ops layer is where that stops being
philosophy. Graceful death is a concrete sequence (checkpoint → reason →
evidence → registry), ungraceful death is detectable (brain-death gap), and the
watchdog exists to convert impending bad deaths into good ones. A system that
cannot die well cannot be trusted to run long.

**Safety governance for adaptive systems.** A system that can change its own
parameters, run for days, and attach to another runtime needs a control layer
that is explicit, fixed, and outside the learning loop. Governance here is
deny-by-default: bounded/simulated/observe-only/dry-run are allowed; anything
that adapts actively, runs long, or reaches outward is gated. The point is not
to make the system safe by hoping — it is to make "what is this run allowed to
do?" a question with a written, audited answer before the run starts.

**Human-in-the-loop approval.** The hard rule is that nothing bypasses a human.
High-risk capabilities (active plasticity, long soaks, publishing suggestions)
produce a `PolicyDecision` that stays *denied* until a named operator records
an approval. The approval ledger is deliberately not a security system — there
is no authentication — because the threat model is "a researcher accidentally
launches something they shouldn't", not "an attacker". For that threat,
making the human step explicit and recorded is the right tool.

**Auditability.** Every governance decision, approval, risk assessment,
emergency stop, operator note, runbook, and checklist becomes a JSONL row.
Combined with the operational incident log and the plasticity audit, a finished
run can be fully reconstructed: what was allowed, who allowed it, what changed,
what was blocked, and how it ended. Auditability is what lets a cautious
project move toward longer runs — you can always answer "what happened?".

**Claim discipline in consciousness-inspired AI.** The most likely failure of a
project like this is not technical; it is rhetorical — quietly drifting from
"consciousness-inspired signal flow" to "the system is conscious". `ClaimGuard`
makes that drift mechanical to catch: it scans generated reports for
unsupported claims about inner states and offers grounded replacements
("produced a Desire signal", "maintained continuity metrics"). The discipline
is structural, not a matter of remembering to be careful.

**Why emergency stop is part of the architecture, not an accessory.** A stop
button bolted on at the end tends to be the thing that does not work when it
matters. Here the emergency stop is a first-class component: always available
regardless of permissions, routed through the same graceful shutdown path that
checkpoints and records why it stopped, reachable out-of-band via a sentinel
file, and structurally incapable of killing the process or deleting data. A
system intended to run continuously must have a stop you can trust before it is
allowed to run long — so the stop is designed first, not last.

**Pilot design for adaptive systems.** An adaptive system's first deployment
should change the *environment*, not the system: Pilot-0 runs exactly the
substrate that passed the benchmarks, inside a harness that adds governance,
supervision, readiness gates, and reporting. If a pilot needs new capability
to succeed, that is a finding about scope, not a reason to patch capability
into the pilot layer.

**Read-only sensing before action.** The ladder matters: simulate, then
observe real data without acting, and only much later consider acting. The
read-only stream profile is the second rung — external structure enters the
substrate (real timing, real gaps, real noise) while the action surface stays
exactly zero. Most of what one wants to learn about an adaptive system in the
wild (does it stay healthy? does it stay bounded? does its learning signal
survive contact with messy data?) is observable from this rung.

**Staged deployment.** Each profile is a stage with its own risk level,
permissions, checklist, runbook, and exit criterion (the pilot report's
recommendation). Graduation is a human decision over recorded evidence —
`ready_for_next_stage` is a string in a report, not a transition the system
can take by itself.

**Bounded real-world observation.** Even pure observation is bounded here:
explicit input files only, line-size limits, validated contracts, bounded
tails, and a supervised step budget. Unbounded observation is a resource
leak at best and an unreviewable experiment at worst; bounding it keeps every
pilot a finite object that can be replayed, audited, and compared.

**Why a controlled pilot harness comes before autonomy.** Autonomy is not a
feature to add; it is a set of controls to *remove*, one at a time, with
evidence. Building the pilot harness first inverts the usual failure mode:
instead of an autonomous system retrofitted with brakes, this is a braking
system into which capability is gradually admitted. The harness — not the
substrate — owns the run modes, and that ownership is structural.

**Memory replay.** Replaying remembered windows through the substrate is the
cheapest way to squeeze more signal out of bounded experience: the same
events, revisited under different selection pressure (recent, high-valence,
high-error, silence), exercise pathways that a single pass touched once.
Here replay runs in deterministic sandboxes — same seed, copied state — so
the question "what would the substrate do with this again?" is answerable
without contaminating what the substrate actually is.

**Sleep-inspired consolidation.** Biological sleep consolidates; our
engineering analogue distils the trace into explicit schemas (repeated
pattern→action pathways with support counts and average valence) during
windows when nothing external is happening anyway. The inspiration is the
scheduling idea — use quiet time for maintenance — not the biology, and the
docs say so at every opportunity.

**Predictive processing.** A one-step frequency/recency predictor is almost
embarrassingly simple, and that is the point: if rolling accuracy is high,
the input has exploitable regularity; if it collapses, the world changed.
Anticipation accuracy is therefore less a capability metric than a
*world-regularity* metric — and its complement feeds directly into unknown
pressure.

**Counterfactual simulation.** "What if the valence had been inverted?" is a
question a trace can answer offline: transform the window, replay both
versions into twin sandboxes, measure divergence. High divergence means the
behaviour hinges on that variable; low divergence means it is robust to it.
The discipline is in the labels — every counterfactual is marked simulated
and validated against leaking into real memory or outbound channels.

**Uncertainty / unknown pressure.** Solaris_Ai's Mysterium names the pull of
the unknown; the implementable core is a number with receipts: pressure
rises for listed reasons (misses, novelty, unexplained error, divergence)
and falls for listed reasons (hits, stability, consolidation). The receipts
matter more than the number — "unknown pressure is 0.62" is only useful if
the next line says why.

**Why this is not a claim of subjective dreaming.** The dream cycle replays
recorded data through a copy of a small recurrent network and measures
numeric divergence. Nothing in that sentence involves experience, and the
system never says otherwise: ClaimGuard scans every latent report, the
mandatory limitations spell out the framing, and the language layer is
hard-coded to say "during offline replay, the system simulated…" rather
than "the system dreamed…". The sleep/dream vocabulary is an engineering
mnemonic for *when* and *how* the processing runs — not a description of
what it is like, because it is not like anything.

**Neuro-symbolic memory.** A reservoir is superb at reacting and hopeless at
being asked "what do you know?". A symbolic graph is the opposite. Pairing
them costs almost nothing here — the graph is dictionaries fed by events the
system already records — and buys the property research needs most:
inspectability. Every node is countable, every edge cites its evidence, and
the whole memory diffs cleanly between runs.

**Knowledge graphs in cognitive architectures.** The classic risk is
ontological inflation: graphs that grow nodes faster than evidence. The
discipline used here is deterministic identity (same type+label is the same
node, observation accumulates), capped confidence, deny-by-default safety on
what may become a node at all, and unknown nodes as first-class citizens —
the graph records what it failed to extract with the same care as what it
extracted.

**Causal candidates vs proven causality.** Temporal precedence,
co-occurrence, feedback, and even embodied intervention are evidence
*streams*, not proofs. The model keeps them separate, weights intervention
highest (it is the closest thing to an experiment the system has), marks
counterfactual evidence as simulated, caps confidence below certainty, and
labels every edge `causes_candidate`. The honest vocabulary is structural:
there is no edge type that asserts proven causation.

**Graph pruning as synthesis.** Solaris_Ai's synthesis-through-subtraction
applies cleanly to symbolic memory: a graph that only grows becomes noise.
Weak one-off structure is proposed for removal, redundant unknowns merge
into their typed twins, and — the research-critical part — subtraction is
dry-run by default, evidence-preserving, reversible, and governance-gated
in production. Forgetting is a deliberate act with a paper trail.

**Why symbolic memory complements reservoir substrates.** The reservoir's
state is a point in a high-dimensional space that nobody can read; the
graph is slow, low-dimensional, and legible. The substrate decides *now*;
the graph remembers *usually*. Predictions flow from graph counts into the
anticipation tracker (fast loop borrows slow structure), and prediction
misses flow back as unknown pressure (slow structure learns where it is
wrong). Neither layer claims understanding — together they make the
system's behaviour explainable at two timescales.

**Homeostasis in cognitive architectures.** Regulation-first designs put a
layer between sensing and acting that asks "what is out of range?" before
"what should be done?". The payoff is coherence under conflicting signals: a
single normalized variable space means energy, safety, novelty, and memory
pressure are comparable numbers, and a fixed resolution ladder means the
same contradiction always resolves the same, inspectable way.

**Drive-based behaviour.** Drives are the classic middle layer between needs
and actions: slow-moving pressure channels that bias many decisions rather
than commanding one. Implementing them as a ten-element decaying vector
keeps them honest — a drive here is literally a float you can print, feed to
the substrate as modulation, and watch decay when its needs go quiet.

**Active inference parallels.** Squint and the loop resembles active
inference: deviations from target ranges (prediction errors about preferred
states) drive policy biases that should reduce those deviations. We
deliberately implement the cheap half only — explicit variables, counted
needs, fixed ladders — and not the full free-energy machinery; the parallels
are a map for future work, not a claim of equivalence.

**Valence as feedback polarity.** Calling the running sign of feedback
"valence" rather than "mood" is not pedantry; it is what keeps the metric
useful. A polarity with attributed evidence ("blocked_action: -0.3") can be
debugged; an emotion label cannot. The same discipline applies everywhere in
this layer: pressure, not desire; recommendation, not decision.

**Why needs are not free will.** Every number in this layer is a deterministic
function of recorded conditions; every suggestion passes a deny-by-default
safety list and a fixed conflict ladder; every override attempt is refused by
construction; and the one dramatic-sounding output — safe_shutdown_recommended
— is an incident row that a watchdog may ignore. A system whose "wants" are
auditable pressures with no execution path is precisely a system without
will, and the documentation says so wherever the words could mislead.

**Executive function as arbitration, not agency.** The cognitive-science
term "executive function" names a family of control processes — selection,
inhibition, working memory, set shifting — none of which requires agency to
implement. Ours is a scoring function with a queue in front and a trace
behind: fourteen visible components, penalties that structurally dominate
utility, and a fallback that prefers doing nothing over forcing a choice.
The selection is deterministic given its inputs, and that determinism is the
research property — the same conflict resolves the same way, every time, and
you can read off why.

**Inhibition as a first-class output.** Most decision systems report what
they chose; the interesting evidence is usually in what they suppressed.
Treating inhibition as a recorded act — rule, family, reason, kept on the
candidate — turns "why didn't it explore?" from a debugging session into a
table lookup. The five-family structure (governance, safety, resource,
context, conflict) also makes misconfiguration visible: a run whose
inhibition ledger is dominated by one family is a run whose constraints are
fighting its configuration.

**Prospection without confabulation.** The failure mode of consequence
estimation is inventing consequences. The engine here refuses to: estimates
exist only where evidence exists (world-model valence, habit weights, a
sandboxed world), every result carries its basis and a capped confidence,
and "unknown" is a respectable answer that increments a counter rather than
a gap to be papered over. Prospection runs against deep copies — the real
world state is never touched by imagining.

**Why short-horizon planning only.** Long-horizon autonomous planning is
where suggestion systems quietly become agents: a 50-step plan is a policy,
and a system executing its own policy is no longer arbitrating among
suggestions. Capping plans at three steps (hard max five, refusal not
truncation) keeps the planner inside the suggestion regime — long enough to
test sequencing in simulation, too short to constitute autonomous conduct.

**Emergency mode as a one-way door (from the inside).** The executive can
enter emergency mode but not leave it; only ops or governance clearing the
underlying condition restores arbitration. This asymmetry is the safety
property: a control layer that could reason itself out of its own
restrictions would make every restriction advisory. `can_override_emergency_
stop()` returning a hard-coded `False` is the whole design, stated as code.

**Why arbitration is not will.** Every selection is a deterministic function
of recorded pressures, evidence, and penalties; every suppression carries
its rule; every output is a suggestion with `committed=False` enforced at
construction; and the strongest thing the layer can do when everything is
blocked is ask a human to look. A chooser whose choices are auditable
arithmetic with no execution authority is precisely a system without will —
and the reports are required to say so.

**Ego as an operational boundary model.** Solaris_Ai calls Ego a
necessary forced illusion; the implementable core of that idea is a
ledger of differences — what belongs to the running system, what belongs
to the environment, what is only simulated, only suggested, only
remembered, unknown, or forbidden. Implemented as sixteen named
boundaries with recorded crossings, that ledger does real safety work:
the questions that most often break agentic systems ("was that an
instruction?", "did that actually happen?", "did we do that?") all become
table lookups.

**Self-models in cognitive architectures.** A self-model earns its place
not by being rich but by being *load-bearing*: other layers must consult
it. Here the executive asks it for action authority, homeostasis converts
its uncertainty into pressure, pilot safety fails on its violations, and
the Inner MAP publishes it. Crucially the dependency is one-way — the
self-model can add inhibitions and raise pressure, but it can grant
nothing, which is what keeps a self-model from quietly becoming a second
decision-maker.

**Body schema in simulation.** The body schema answers "what can act,
and where?" with data: a simulated grid body with declared actions,
sensors, effectors, and `simulation_only` authority. Declaring the body
simulated everywhere it appears is not modesty; it is the mechanism that
makes "no real-world actuation" checkable — any action shaped like
hardware fails the schema before it reaches an arbiter.

**Ownership attribution.** Most prompt-injection-style failures are
attribution failures: text from a stream treated as an instruction, an
observed action treated as one's own, a simulation treated as the world.
Eleven fixed attribution categories with negative guarantees (stream is
never executable; operator input needs the operator interface;
counterfactuals stay counterfactual; suggestions are never committed)
turn that whole failure family into explicit, testable rules.

**Dimensional comparison.** Two events can differ in when, where, with
what authority, on what evidence, with what certainty, and at what risk —
six axes, each a short ordered list. Deterministic index distance is
laughably simple next to embeddings, and that is the argument for it: the
comparison is auditable, stable across runs, and its explanation is the
computation itself, not a story about one.

**Why self-report does not imply consciousness.** A system that prints
"identity continuity 0.84, perspective latent_offline_replay, 1 boundary
violation" is reporting measurements of its own machinery, exactly as a
thermostat reports temperature. The report pipeline enforces the
distinction mechanically: deterministic templates, no first-person
statements, mandatory limitations, and two scanners (ClaimGuard plus the
identity-claim scan) that refuse to write "I am conscious", "I want", or
"same self" at all. Self-description is cheap; the discipline is in what
the system is structurally unable to say.

**Human-in-the-loop interfaces for adaptive systems.** An adaptive system
needs an operator interface *more* than a static one — drift, incidents,
and approvals all assume a human can see in and reach in. The design
constraint is that the reaching-in must be narrower than the seeing-in:
here every query is free, while every state change is typed, confirmed,
scoped, and transcribed. The interface widens observation and narrows
intervention.

**Command/query separation.** The oldest interface discipline (CQS) does
disproportionate safety work in this setting: queries cannot change
state, so they need no gates; commands form a closed typed set, so they
can all be enumerated, validated, confirmed, and refused by name. The
moment "show status" and "shut down" travel the same code path with the
same authority, every text becomes a potential command — separating them
makes the dangerous class small and auditable.

**Language as interface vs authority.** The failure mode of language-first
systems is that whoever controls the text controls the system. The
gateway inverts that: text is classified into intent, intent maps onto a
closed command set, and the command set is gated by governance, ego
boundaries, and safety validators that language cannot address at all.
"Disable governance" is not a hard case — it is an unsafe *input class*,
refused before routing.

**Grounded responses.** A response is grounded when its content can be
traced to recorded state — evidence references on every answer, "the
system has no evidence for that answer" as a first-class reply, and an
explicit distinction between *executed* and *recorded as a request*. The
grounded-response ratio is a metric precisely because ungrounded fluency
is the cheapest thing a text interface can produce and the most expensive
to debug.

**Why deterministic dialogue comes before LLM-based conversation.** An
LLM front-end would add fluency and ambiguity in equal measure — and
ambiguity at the operator boundary is attack surface (prompt injection is
just attribution failure with better grammar). Building the deterministic
layer first fixes the contract: classification before effect, closed
command set, channel attribution, scanned output. If an LLM is ever added
for parsing, it slots in *above* this layer and inherits its gates; it
does not replace them.

**LLMs as interface layers.** The useful framing for a deterministic
cognitive system is the compiler one: the LLM is a pretty-printer, not a
parser of authority. Everything upstream of it — classification, safety,
governance, arbitration — runs identically whether the adapter is on,
off, or hallucinating, which makes the adapter's worst case a wording
regression rather than a behaviour change. That property is only true
because it was built in structurally; it cannot be patched in later.

**Grounding validation.** Without NLP machinery, grounding checks must be
blunt: number provenance, forbidden-phrase scans, conversion detection,
uncertainty preservation — and the crucial design rule that *uncertain
means failed*. Blunt heuristics with a fail-closed default beat clever
ones with a fail-open default in exactly the situations that matter,
because the model's failure mode (fluent invention) is precisely the one
heuristics flag as "this number came from nowhere."

**Paraphrase vs authority.** A paraphrase changes wording under an
invariance constraint: same facts, same numbers, same warnings, same
limitations, same evidence references. Stating the constraint as code
(structural checks after generation) rather than as a prompt instruction
is the difference between asking a model to behave and not needing it to.

**Confabulation risk.** LLMs produce confident text whether or not it is
anchored to anything — for an operator interface, the dangerous output is
not the wrong answer but the *plausible* one. The mitigations here are
layered: facts pre-scanned in, contracts that demand refusal over
invention, grounding heuristics that trace every number home, ClaimGuard
on the way out, hashes in the audit log, and a deterministic original
that is always one fallback away.

**Why deterministic cognition/safety must precede LLM dialogue.** Adding
an LLM to a system without a deterministic spine gives the model the
spine's job; adding it to this system gives the model a typesetting job.
The nineteen prior layers fixed what the system knows, decides, refuses,
and reports — so the twentieth could be allowed near the text without
being allowed near the truth. That ordering is the experiment's actual
finding: language models are safe to add last, and only last.

**Developmental learning.** A training job has a dataset, a loss, and an
end; a developmental process has a history. Framing Solaris-AI-NN's first
learning mode as months of autonomous runtime — rather than any form of
teaching — commits the project to its own thesis: long-running weak
adaptation over lived experience, with the system's structure as the
record of what its history did to it.

**Long-horizon adaptation.** The interesting failure modes of adaptive
systems are slow: drift that compounds, memory that silently saturates,
habits that ossify, accuracy that degrades over weeks. None of them are
visible in a 150-step benchmark. The developmental runtime exists to make
slow phenomena observable cheaply — simulated time for rehearsal, real
time for the actual experiment, identical instrumentation for both.

**Memory consolidation over months/years.** Biological memory does not
keep raw experience; it keeps progressively compressed, progressively
schematic derivatives, plus a few vivid landmarks. The hot/warm/cold/
fossil ladder is the engineering version: detail decays on a schedule,
schemas persist, and the landmarks (firsts, violations, recoveries) are
kept verbatim forever. The non-negotiable constraint is auditability —
every compression leaves an evidence summary, so forgetting is always a
recorded act.

**Autobiographical memory in cognitive architectures.** A system that
runs for months needs an answer to "what happened to you?" that is
shorter than its trace and truer than its current state. Grounded,
templated, observational history rows — with simulated time explicitly
marked — give exactly that, without the trap: autobiographical *records*
imply storage and retrieval, not remembering in any experiential sense,
and the writing voice is structurally prevented from claiming otherwise.

**Structural change vs data accumulation.** The cheapest way for a
long-running system to look like it is developing is to grow its
database. The growth monitor's whole purpose is to refuse that
equivocation: node counts rising while schemas, habits, and pruning stay
flat is *accumulation*; consolidation, stabilization, and subtraction are
where structure actually changes. A stagnation label is as valid a
finding as a growth label — the measurement is the point.

**Why human feedback is postponed.** Teaching signals are powerful and
contaminating: once an operator's corrections shape behaviour, every
structural change is confounded — did the system adapt to its world or to
its teacher? Running the first months teacher-free keeps the central
question clean (is it different because of what it lived through?), and
it forces the architecture to be honest about what persistence alone can
do. Human feedback can be layered on later; un-confounding it later is
impossible.

**Language emergence.** Every account of language origins begins with
differentiation: some recurring chunk of experience becomes worth
marking apart from the rest. The proto-language layer implements exactly
that minimal step — repetition above a threshold earns a deterministic
internal token — and deliberately nothing more. Whatever else language
is, it is downstream of having signs at all.

**The symbol grounding problem.** Symbols that only point at other
symbols mean nothing; Harnad's classic problem is escaping the
dictionary loop. Here every symbol is born already grounded — in a
recorded signal pattern, need, action, reaction, boundary, or unknown —
and grounding is the *definition* of meaning in this system: a sign
means what it reliably co-occurs with, operationally, with ambiguity
measured rather than resolved by fiat.

**Proto-language vs human language.** The distance is the point. No
phonology, no recursion guarantee, no pragmatics, no speaker — just
signs, sequences, and tested regularities. Calling the sequences
"proto-syntactic structures" rather than grammar is not modesty; it is
accuracy, and the one query the system answers with a flat "No" is
"is this human language?"

**Compression as naming pressure.** Why name anything? Because a name is
cheaper than the thing it stands for. The compression evaluator makes
that folk intuition a metric: a symbol that lets twelve repeated events
fold into one token with a repeat count has earned its existence in
bytes. The constraint that safety incidents stay verbatim is the
counterweight — some things must never become cheap to store.

**Prediction as semantic test.** A symbol system that carries structure
should make the future cheaper to guess. Markov-style next-symbol
prediction against a frequency baseline is the lowest-compute honest
version of that test, and its honesty is structural: shuffled noise
produces no improvement and the report says so. Meaning that does not
help prediction anywhere is indistinguishable from decoration.

**Enfant sauvage framing.** A child raised without language exposure
still differentiates, names privately, and routinizes — what they lack
is the social loop that standardizes signs into a shared code.
Solaris-AI-NN is deliberately in that pre-social stage: its signs answer
to its own experience and its own utility metrics, not to a community of
speakers. That makes the symbols strange and private, and it makes them
*evidence* — nothing about them can have been imitated.

**Why human teaching is postponed.** The moment an operator labels
things, the symbol system inherits human ontology and every emergent
structure is confounded. Keeping the first symbols teacher-free keeps
the research question clean: what sign system does repetition plus
utility produce on its own? Human alignment of the vocabulary can be
layered on later; un-teaching it later is impossible.

---

## Phase 23 — Developmental nursery and stimulus ecology

**A developmental system needs an ecology, not a teacher.** Phases 21–22
gave the system time (a lifetime across restarts) and the beginning of
signs (proto-symbols from repetition). But repetition needs *something to
repeat*, and so far that something was a thin synthetic stream. Phase 23
supplies the missing piece: a controlled artificial world with the texture
real development requires — recurrence and absence, scarcity and plenty,
rhythm and arrhythmia, novelty that fades into familiarity, danger and
reward analogues, boundaries, rare events, slow seasonal drift, long quiet
periods, pattern breaks, delayed consequences, and recoverable disruption.

**Why a world rather than a dataset.** A dataset is a fixed answer key
sampled i.i.d.; a world is a non-stationary process with rhythm, memory,
and consequence. Habits only mean something against a world that rewards
them sometimes and not others; absence symbols only form where signals were
expected and did not come; delayed-consequence association only matters
when cause and effect are separated in time and *not* labelled as a pair.
The ecology is built to make those structures *available to be discovered*,
never to hand them over.

**Silence as a feature, not a gap.** The single most deliberate design
choice is that the nursery's `stimulus_provider` returns `None` on
absence/silence steps. It would have been easy to emit an explicit
"absence" signal; instead the world simply goes quiet, and the runner's own
continuity machinery (the latent "I exist!" pathway) must carry the system
through. Long quiet periods are where latent cognition earns its place, and
where the system's persistence is tested against nothing at all.

**Anomalies are perturbations, not errors.** Every anomaly is logged with
`is_error=False`. This is a research stance as much as a flag: an
established pattern that suddenly breaks is not a bug in the world or a
failure of the system — it is information. Conflating perturbation with
error would teach the system (and the operator reading the report) exactly
the wrong lesson about what a surprising world is for.

**The discipline of no labels.** The hard rules forbid correct-answer keys,
command-shaped payloads, human feedback masquerading as ecology, and LLM
text as the learning environment — and the ego layer attributes every
nursery event as generated-by-nursery, never operator, never human
feedback, never real-world. The same logic as Phase 22's teacher-free
symbols applies one layer down: the moment the world contains answers, the
emergent structure is confounded by them. A clean question demands a world
that pressures but never tells. Adaptation to that world can be measured;
it cannot be taught here, and that is the point.

---

## Phase 24 — Active perception and intrinsic exploration

**From being fed to sampling.** Phases 1–23 built a system that *reacts* to a
world the ecology supplies. Phase 24 takes the next step a developing system
must take: it begins to *choose how it looks*. The same stimulus world is now
something the system can sample — look, focus, replay, consolidate, seek
novelty, seek absence — rather than only receive. The principle is simple and
load-bearing: a developmental system should not only react to stimuli, it
should regulate its own exposure.

**Curiosity as uncertainty reduction, not wanting.** The hardest discipline
here is naming. It would be easy, and wrong, to call the drive that makes the
system sample an unknown region "curiosity" in the human sense and let the
word do unearned work. We keep curiosity strictly as an *intrinsic sampling
pressure*: a scalar that rises with unresolved unknown pressure and falls with
safety load, computed from existing metrics, and explicitly documented as not
a desire, feeling, or personality. The intrinsic-motivation literature
(novelty, prediction-error, information gain as reward) is the lineage; the
anthropomorphism is deliberately left out.

**Information gain in a low-compute system.** We cannot run a Bayesian
value-of-information computation on every candidate. So information gain is a
heuristic: per-action affinities for the pressures they tend to relieve,
scaled by how present that pressure is and how much evidence supports the
estimate — and every estimate carries a confidence and an uncertainty, with
the expected gain capped when evidence is weak. The honest move is the
*observed* gain: after an action runs, we measure the actual before/after
change in Mysterium, prediction, and ambiguity, and record it next to the
estimate. Over time the gap between expected and observed is itself a
finding.

**Exploration vs safety.** The whole layer is built so that exploration can
never win against safety. Curiosity is damped to near zero by emergencies,
critical health, exhaustion, and runaway novelty; the policy is forced into
emergency or recovery mode by those same conditions; the safety validator
refuses real-world targets, stream modification, sidecar commits, and
unbounded loops; the ego classifies every sample by boundary; and sampling
actions still pass through executive inhibition as ordinary suggestions. When
no safe sampling exists, the answer is `no_sampling_action`.

**Why this is not real-world autonomy.** Self-directed sampling sounds close
to agency, so the boundary is stated plainly: every sampling action is
simulation-only, internal-only, read-only, or sidecar-observe-only; nothing
reaches the network, the OS, a browser, hardware, or a committed Solaris_Ai
Action; no LLM makes any exploration decision; and the loop is bounded.
Choosing where to look inside a bounded simulation and one's own memory is a
developmental capability — it is emphatically not permission to act in the
world, and the architecture keeps those two things apart on purpose.

---

## Phase 25 — Hypothesis engine and bounded self-experimentation

**Self-experimentation in adaptive systems.** A system that only samples
(Phase 24) still answers questions the environment happens to pose. Phase 25
lets it pose its own: form a candidate ("pattern A may predict B"), design a
bounded test, run it in simulation/internal/read-only scope, and read the
evidence. This is the smallest honest version of an internal scientific
method — generate, test, update — implemented at low compute and kept
strictly bounded.

**Falsification first.** The engine is built around weakening and
falsification, not confirmation. It is easy to build a system that
accumulates support for whatever it already leans toward; the discipline here
is the opposite. Confidence moves in small bounded steps, one success rarely
promotes a hypothesis, offline-only support is capped below a ceiling, and a
clear contradiction can falsify outright. The most useful outcome of a test
is often "falsified" — a candidate removed — and the report shows the
falsified set as prominently as the supported one.

**Curiosity and hypothesis generation.** Phase 24's curiosity (an intrinsic
uncertainty-reduction pressure) is what makes hypotheses worth forming and
testing: the source scanner is, in effect, curiosity made specific. Where
curiosity says "this region is uncertain", the hypothesis engine says "here
is a concrete, falsifiable guess about that region, and here is the bounded
test that would settle it". The two layers are the same impulse at different
resolutions.

**Causal candidates vs proven causes.** The engine never claims a cause. The
strongest label it can earn is `causes_candidate` in the world model, and
only from real or nursery-simulated evidence above a threshold, behind an
approval-gated permission. A supported hypothesis is a hedged, evidence-backed
association, explicitly not a proof — the reports and the wording enforce
this, because the gap between correlation a system can measure and causation
it cannot is exactly where overclaiming begins.

**Source-scoped evidence.** Every piece of evidence remembers where it came
from. Latent-replay and counterfactual evidence is marked offline and can
never be treated as a real observation of the running system; nursery and
read-only-stream evidence can support; and the falsification engine respects
the distinction. This keeps the cheap, abundant offline evidence from
silently standing in for the scarce, expensive real evidence.

**Why testing stays bounded and safe.** A system that experiments on its
world is one step from a system that acts on it, so the boundary is stated in
code: no real-world experiment, no OS/browser/network action, no source
rewriting, no sidecar commit, no unbounded test, no test that disables safety
or the emergency stop, and no LLM-generated hypothesis treated as authority.
Hypothesis tests enter executive arbitration as ordinary suggestions and are
inhibited like any other; an emergency blocks all testing. Forming and
testing guesses about a bounded simulation and one's own memory is a
developmental capability — it is not, and must not be confused with,
permission to act in the world.

---

## Phase 26 — Auto-regeneration and long-run state hygiene

**Self-maintenance in long-running cognitive systems.** Every prior phase
adds something that accumulates: traces, symbols, world-model edges, habits,
hypotheses, exploration records, fossil memory. Over months or years of
runtime, accumulation without maintenance is entropy: bloat, staleness,
contradiction, broken references, drift. Phase 26 is the janitor the system
needs to survive its own history — a low-compute loop that detects
degradation and repairs *runtime state* so the long run does not collapse.

**Degradation vs adaptation.** The hardest judgement here is not detecting
change but deciding which change is decay and which is growth. Slow drift is
life; flat-but-calm is often a healthy stable phase; a runaway is genuinely
dangerous. The drift recovery classifier is deliberately cautious: it refuses
to "repair away" healthy adaptation, it does not treat every flat window as
death, and when it cannot tell, it stabilizes and asks for review rather than
acting. Mistaking adaptation for illness would be its own kind of damage.

**Memory hygiene.** Compaction is necessary but dangerous: the easy version
loses exactly the records that matter. So safety incidents, boundary
violations, emergency events, and milestones are never compacted away;
fossil memory is append-first; and compression must preserve a transformation
summary so the *evidence that compaction happened* survives the compaction.
Hygiene that hides what it did is worse than no hygiene.

**Symbol ecology maintenance.** The proto-symbol registry is an ecology, and
ecologies need tending: stale signs marked, duplicates merged, ungrounded
signs flagged, explosion bounded. But symbols are not human words, so hygiene
never renames them, and a stable symbol is never deleted without an archive.
The aim is to keep the sign system legible over a long life, not to curate it
toward human meaning.

**Checkpoint continuity.** Identity continuity is the one place where repair
is most tempting and most dangerous. The checkpoint repair manager can
restore last-known-good *metadata*, but it never silently rewrites identity
history; an ambiguous continuity gap becomes an operator/governance review
request, not a quiet fix. A system that edits its own past to look continuous
is not repairing continuity — it is faking it.

**Why auto-regeneration is not self-programming.** Repairing the state a
program holds is categorically different from repairing the program. This
layer can compact a memory layer, weaken a graph edge, mark a symbol stale,
reset a bounded parameter, roll back the last plasticity update, and quarantine
a corrupt file — all reversible, audited, inside the state directory. It can
never touch a source file, a dependency, Git, the OS, or the network; it
cannot disable governance, ClaimGuard, or the emergency stop; and every repair
passes through the same safety/executive/governance gates as any other
suggestion. Operational regeneration buys long-run survival; it buys no new
authority, and that boundary is the whole point.

---

## Phase 27 — LOGOS fracture/synthesis and complexity regulation

**Contradiction as productive pressure.** Every prior layer treats a
contradiction, an ambiguity, or a failed prediction as something to fix.
LOGOS treats it as something to *use*. A tension between two internal poles
is information: it marks exactly where the system's model is incomplete, and
it is the raw material of structural change. The reframe is deliberate — a
fracture is not, by default, an error.

**LOGOS as an operational tension engine, not authority.** The single most
important design decision is what LOGOS is *not*. It does not decide truth, it
does not resolve the unknown by fiat, and it holds no authority. It detects
oppositions and proposes bounded resolution paths — preserve, split, merge,
synthesize, prune, stabilize, hypothesize, sample, replay, repair, or mark
unresolved — and every one of those is a suggestion that passes through the
same safety/executive/governance gates as any other. Calling it a tension
engine rather than a reasoner keeps the philosophy from leaking into
authority it should not have.

**Synthesis vs destructive merge.** Synthesis is the dangerous half: the easy
version "resolves" a contradiction by deleting one side of it, which destroys
evidence and manufactures false coherence. So synthesis here is reversible and
low-risk by default, contradiction evidence is preserved (edges are marked
ambiguous or weakened, never deleted), a destructive evidence merge is
refused outright, and offline/counterfactual evidence can never justify an
irreversible synthesis alone. A contradiction the system cannot yet resolve is
kept as a preserved, unresolved tension — that is the honest state.

**Complexity regulation.** A system can fail in two opposite directions: it
can go inert (no change, effectively dead) or it can overload (too many
tensions, symbols, edges, and unresolved questions to function). Productive
cognition lives in the bounded middle. The complexity regulator names the
band and recommends a direction — more exploration when inert, more
consolidation when unstable, auto-regeneration when overloaded — without ever
collapsing this into a single "how alive is it" number, which would be both
meaningless and unsafe.

**Preserving unknowns.** The most counter-cultural rule in the layer is that
some tensions should never be resolved. Safety/boundary oppositions, the
known/unknown divide, the habit/novelty pull — these are kept open on
purpose. A system that resolves every tension is a system that has stopped
learning or has started lying to itself about its own gaps. Preserving an
unknown as an unknown is treated as a first-class outcome, with its own
milestone.

**Why LOGOS is not authority.** The Esc process makes the boundary concrete:
under rising instability LOGOS can *request* stabilization, replay,
diagnostics, or even a safe-shutdown review — but it performs none of them.
Esc is an instability signal, not panic and not an emotion; the ops watchdog
still decides. LOGOS gives long-run development structure — a vocabulary for
its own fractures and a disciplined way to propose resolving them — and it
buys exactly no new authority in doing so. That separation is the whole
point.

## Phase 28 — Conscience spine and unified runtime orchestrator

**From a library of parts to a runnable organism.** Through Phase 27 the
project was a set of independent, individually-safe packages. The risk of that
shape is subtle: a collection of correct modules is not the same as a correct
whole, and "we could wire it together" is not the same as "it runs." Phase 28
makes the organism actually run — one process, one spine, one bounded loop —
without surrendering any of the guarantees that made each part safe.

**No module is sovereign.** This is the load-bearing principle. The
orchestrator is not a brain that commands the others; it is a conductor with
no instrument of its own. It owns no action authority. Every action is still
*suggested*, still passes through executive inhibition, Ego boundaries,
safety, governance, and ClaimGuard, and the emergency stop is checked every
step. If the executive module is absent, nothing is committed at all. The
temptation when unifying a system is to let the unifier accumulate authority;
we designed explicitly against that.

**Partial configurations must degrade, not fake.** A real organism keeps
going when a part is missing; it does not hallucinate the missing part. So a
spine phase whose module is unavailable is *skipped with a clear status*, a
handler that raises is recorded as *degraded* and the loop continues, and an
unknown module name in a profile is silently ignored — never stubbed with a
fake that pretends to work. The registry detects availability by import probe
and the integration-health monitor reports honestly whether the whole thing is
healthy, partial, degraded, or failed.

**Bounded by construction; simulated time is not real time.** Nothing runs
unbounded by default. A `RunContext` always carries an authority that is
internal/simulation/read-only/observe — never real-world — and the runtime
safety validator refuses an unbounded run without governance approval, a real
month/year mode without approval, and (importantly) any attempt to label a
*simulated*-time run as a real one. The month-scale profiles are a dry plan
and a simulated slice; there is deliberately **no canned "real month"
profile**, because a real long-scale run should require a human to construct
and approve a context, not click a preset.

**Low compute is a scheduling property, not an afterthought.** The scheduler
runs cheap phases (heartbeat, stimulus, push, reaction, memory) every step and
heavy scans (LOGOS, hypothesis, auto-regeneration, consolidation, reports) at
slower cadences. This is what lets the same spine that smoke-tests in twelve
steps also stand in for a month-scale plan without the compute exploding — and
every scheduling decision is inspectable, so the trade-off is auditable rather
than hidden.

**Honesty is enforced at the report boundary.** The full-system report is the
one artifact most likely to overclaim, so it is the one most tightly guarded:
every line of its narrative passes through ClaimGuard, and it states plainly
that it describes a bounded, simulated, low-compute software process — not a
person, with no real-world authority. Making the organism runnable raised the
stakes on overclaiming, so the guard sits exactly where a run's story gets
told.

## Phase 29 — Pilot-1 month-scale soak protocol

**From "it runs" to "it can be run for a month".** Phase 28 made the organism
runnable in one process; Phase 29 makes it *operable over a long horizon*. The
gap between those two is almost entirely operational: a system that works for a
hundred steps in a test is not the same as one a human can start, observe,
restart, audit, and stop over thirty days. Pilot-1 is that operational frame,
deliberately built as plumbing rather than new cognition.

**The central question is structure vs accumulation.** It is easy to run a
process for a month and point at a pile of logs as evidence of "development."
That is the failure mode the pilot report is designed to resist: its core
section separates *structural change* (new epochs, milestones, phase
transitions, a non-zero structural-change score) from *mere accumulation*
(memory and counts growing with no structural signal). Asking the question
this way keeps a long run honest, because the default human bias is to read
growth as progress.

**Observability has to be cheap and restart-safe, or it will not survive a
month.** The collector appends to JSONL, derives only a handful of signals,
and recomputes nothing expensive each tick; state lives on disk so a restart
resumes rather than restarts. The same discipline drives the stdlib-only
resource budget (no `psutil`): a month-scale run that cannot project its own
disk use will eventually fill a disk, so projection and retention are
first-class, with auto-regeneration consuming the hygiene requests.

**Restart continuity is rehearsed, not assumed.** Long runs *will* be
interrupted. The restart drills simulate graceful restarts, crash gaps, and
checkpoint restores by manipulating metadata — never by killing a process from
a test — and every drill checks identity continuity. The operator runbook
documents the manual equivalents, because the real safety property is that a
human knows exactly how to stop and resume the run.

**Operational safety is layered, never bypassed.** A real month/year run
requires explicit governance approval; the emergency stop is always available
and can never be disabled; simulated-time output can never be relabelled as
real evidence; and evidence is never deleted without an archive. None of these
are new ideas in the project — Phase 29's contribution is to make them hold
across a *long* run, where the temptation to cut corners is highest.

**Why pilot success is not consciousness proof.** This is stated in the exit
criteria, the dashboard, every review, and the pilot report, on purpose.
Operational success means the run completed and left an analyzable
developmental trace. It says nothing about sentience, understanding, or
personhood, and the framework is written so that no artifact it produces can
be mistaken for such a claim.

## Phase 30 — Post-pilot developmental forensics

**A long run is only valuable if it is analyzable.** Phase 29 made the system
runnable over a month; Phase 30 makes a finished run *answerable*. The danger
of long-horizon runs is not that they fail loudly — it is that they succeed
quietly and produce a mountain of logs that nobody can interrogate. The whole
package exists to convert artifacts into evidence-scoped conclusions.

**Accumulation is the null hypothesis.** The single most important discipline
here is refusing to read growth into a graph that is merely going up. More
data, more symbols, more hypotheses, more edges, more complexity — each is, by
default, accumulation. The analyzer only upgrades to "growth" when increases
are accompanied by payoff: compression that holds, ambiguity that falls,
predictions that improve, contradictions that resolve, repairs that stop the
problem recurring. The classification is graded and conservative, and it
returns `inconclusive` whenever the artifacts needed to judge are absent.

**Evidence must point somewhere.** Every structural-change record names the
artifacts behind it, an alternative explanation, a conservative confidence,
and a stability flag — and stability requires persistence across time windows,
not a single snapshot. The evidence ledger refuses to call a claim *strong*
without multiple artifact types or durable persistence, and it highlights
contradicted claims rather than hiding them. This is what keeps a forensic
report from becoming an advocacy document.

**Traceability and reproducibility are part of the science, not an afterthought.**
The trace audit checks that conclusions are backed by raw observability, that
simulated and real-time records stay separated, and that offline/counterfactual
evidence is never presented as observed. The reproducibility packager records
the seed, modules, config, and a checksum manifest — indexing large logs rather
than copying them, and never packaging secrets. Without these, a "result" is
just an anecdote.

**Conservative interpretation is a safety property.** The decision gate makes
`ready_for_pilot2` hard to reach on purpose: it requires no unresolved critical
safety incidents, analyzable artifacts, acceptable reliability, at least weak
structural-change evidence, a managed budget, and intact identity continuity.
Severe regression routes to architecture revision, not to "try again harder".

**Why long-run success is not consciousness proof.** This is repeated in the
exit criteria, the report, the dossier, and the safety validator because the
failure mode is seductive: a system that ran for a month, restarted cleanly,
and "developed" invites the leap to claiming mind. The post-pilot layer is
built so that no artifact it produces can support that leap. It evaluates
operational continuity, traceability, and structural-change proxies — and says,
plainly and everywhere, that it cannot evaluate consciousness, sentience,
understanding, or life.

## Phase 31 — Read-only sensory membrane

**The world may enter the system; the system may not act on the world.** This
single sentence is the whole design. Pilot-2 asks whether Solaris-AI-NN
develops differently when exposed to a less artificial, more variable
environment than the nursery. The danger of "real input" is that it tempts
"real output" -- so the membrane is built so that input can flow in while
actuation remains impossible by construction, not by policy alone.

**Read-only is enforced in depth, not declared once.** Source configs are
read-only invariants (you cannot even configure write access), the
read-only contract validator and the membrane safety validator both reject
writes/deletes/renames/exec/network/device-capture, adapters only open files
for reading and never modify them, and sources must live inside explicitly
allowed roots. Defence in depth matters here because a single leak would turn
a sensor into an effector.

**Environmental text is not an operator command.** This is the most subtle
boundary. A text stream can contain anything -- including strings that look
like shell commands or instructions. The membrane classifies every text line
as a *textual environmental stimulus* with an explicit `is_operator_command:
False` tag, and Ego attributes it as `read_only_environmental_input`, never as
the operator channel. The system may later form proto-symbols around recurring
text, but the input words are never the internal symbols, and the text is
never executed.

**Provenance is mandatory.** Every event carries where it came from (source,
path hash, raw-line hash, adapter, read-only-validated, simulated vs real,
trust level). An event without provenance is not admissible. This is what lets
the post-pilot forensic layer later distinguish a nursery-only run from a
read-only-membrane run, and a simulated source from a real one.

**Why actuation is postponed (again).** It would be easy to add a tiny
"respond to the environment" hook. We do not, because the project's safety
posture is that capability is added only after the previous layer is observed,
analyzed, and trusted. Pilot-2 is the grounding step: expose the developmental
process to a richer, read-only world and measure whether that changes its
development -- before any question of acting on that world is even raised.

**Nursery vs real read-only exposure.** The nursery is a generated, artificial
world; the membrane is read-only environmental input. Mixed mode keeps the two
strictly separated by attribution, so any developmental difference can be
traced to the source. Camera and audio remain metadata-only here -- no OCR, no
ASR, no image analysis -- because adding heavy multimodal processing would
both break the low-compute principle and invite overclaiming.

## Phase 32 — Pilot-2 read-only environmental soak

**Does the environment change development?** Pilot-1 asked whether the system
develops at all over a long run; Pilot-2 asks a sharper question -- whether
read-only *environmental* exposure produces different structural development
than the artificial nursery. The answer must come from comparison, not
assertion, which is why the whole layer is organized around explicit arms
(nursery-only, sensory-only, mixed) and cautious deltas.

**One-way, by construction.** The entire risk of "real input" is that it
invites "real output". Pilot-2 keeps the membrane strictly one-way:
environment → Solaris-AI-NN, never the reverse. Sources are read-only,
disabling a source only changes its status (never deletes it), and sensory
text is attributed as environmental input, never an operator command. The
decision gate has no "act on the environment" option at all; a Pilot-3
limited-embodiment suggestion, if it ever appears, is planning-only.

**Provenance is the grounding evidence.** Grounding here is operational
association, not understanding -- so the evidence that a structure is grounded
is precisely its provenance plus persistence and cross-module support. A
proto-symbol that recurs across a provenanced source over time, and that
improves prediction or compression, is graded "moderate" or "strong"; one
without provenance is "unsupported". Input words are never the internal
symbols.

**Source reliability is a first-class signal.** A real(istic) environment is
noisy. The reliability monitor classifies each source (reliable /
noisy-but-useful / unstable / malformed / unsafe) so that a noisy source can
stay if it is bounded and useful, while an unsafe source must be disabled. This
keeps the comparison honest: a difference driven by a malformed source is not
a developmental difference.

**Cautious interpretation is mandatory.** Every comparison is reported as an
observed association from a single run, never a proven cause; a missing
comparable arm yields "inconclusive"; and the post-pilot classifier
distinguishes improved-grounding from added-noise-only from caused-overload.
The point is to resist the pull toward reading any change as progress.

**Why actuation is still postponed.** The same discipline as every prior phase:
capability is only added after the previous layer is observed, analyzed, and
trusted. Pilot-2 is the grounding step. Whether the system should ever act on
an environment is a separate question that Pilot-2 deliberately does not open;
it only measures whether read-only exposure changes how the system develops.

## Phase 33 — Pilot-3 motor membrane and actuation firewall

**The opposite boundary, deliberately.** Pilot-2 built the inbound membrane
(read-only input). The obvious next question is whether the system can *act*,
and the obvious danger is that "real action" is exactly the capability whose
risk has been deferred since Phase 1. Pilot-3 resolves the tension by separating
two things that are usually conflated: forming an action intention and executing
it on the world. Solaris-AI-NN may do the former freely; the latter is
structurally impossible. The whole design follows from one sentence:
Solaris-AI-NN may form action intentions, simulate their consequences, write
action traces, and act inside sandbox worlds -- but it may not act on the real
world.

**The firewall is a structure, not a setting.** A safety control that can be
turned off is a safety control that *will* be turned off. So the
`ActuationFirewall` has no off switch: `enabled` is a read-only property that
returns `True`, and `disable()` raises rather than complying. Real-world
authority is not a permission the system lacks-by-default; it is a value that is
*forced* to `False` on every `MotorAction` and every result, and a real-world
scope is representable only as `forbidden_real_world`, which is never in the
*runnable* set. The non-actuation proof score is `0.0` the moment any of these
invariants is violated. This makes "no real-world action" an auditable property
of the code, not a promise in a comment.

**Simulated action is not real action.** The most important discipline is
refusing to let the vocabulary drift. The membrane lets the system "act", but
every actuator is simulated, every consequence is simulation-scoped, and every
report says so. A blocked action is not an executed action; a mispredicted
consequence seeds a hypothesis rather than a correction to the world; and action
selection is described as a mechanism, never as free will, agency, or choice.
The GridWorld is reused as the first sandbox body precisely because it is
already understood to be a toy -- there is no temptation to read its outcomes as
real.

**What it measures.** Like every prior pilot, Pilot-3 is an instrument, not a
milestone toward autonomy. The decision gate has no "act on the real world"
option: a real-world authority leak routes to *revise the firewall*, action
loops route back to read-only, and even a clean, predictive, well-grounded
simulated run routes only to a *longer simulated* embodiment. Whether the system
should ever have real actuation remains a separate question that Pilot-3, by
construction, does not open.

## Phase 34 — Pilot-3 simulated embodiment soak

**The experiment, not just the boundary.** Phase 33 built the motor membrane
(the outbound boundary). Phase 34 builds the experiment around it: a proper soak
protocol that asks whether *simulated* action/reaction loops ground structure
more than perception alone. It is the deliberate mirror of Pilot-2 — where
Pilot-2 compared nursery vs read-only sensory exposure, Pilot-3 compares
read-only perception vs simulated action vs mixed, with the same discipline of
cautious, single-run, observed-association language.

**Action grounding is operational and simulation-scoped.** The temptation is to
read a system that "acts" and "learns from consequences" as embodied or
competent. The analyzer refuses that: grounding is graded from repeated
action/reaction loops, improved prediction, symbol-action-consequence links, and
reduced Mysterium — and a strong result confined to one sandbox context is
flagged `overfit_to_sandbox`, not `strong`. Action-grounded proto-symbols and
world-model edges are tagged simulation-scoped and never promoted to real-world
structure.

**Action/reaction loops.** The GridWorld body lets the system close the loop:
form an intention, run it in simulation, observe the simulated reaction, and
compare it to the predicted consequence. Mispredictions seed hypotheses (scoped
`simulation_only`); the desire to act against the firewall's prohibition is kept
as a preserved LOGOS action/inhibition tension rather than resolved by acting.

**Non-actuation proof.** Every soak ends with a read-only firewall audit and a
proof-of-non-actuation: every executed action has a ledger record, no action
carried real-world authority, no source was modified, and real-world actions
executed is zero. Any leakage is a critical finding that blocks advancing and
routes the decision gate to *revise the firewall* or archive/stop.

**Sandbox overfitting.** A recurring worry is mistaking sandbox fluency for
competence. The analyzer, the weekly review, and the post-analysis all carry an
explicit sandbox-overfit signal, and the decision gate responds to it by varying
the sandbox or adding read-only sensory sources rather than by trusting the
result.

**Why real actuation is still postponed.** The same discipline as every prior
phase. Pilot-3 grounds action in simulation only; whether the system should ever
have real actuators is a separate question that Pilot-3 does not open. Pilot-4
can be *prepared* only as a planning phase, and real-world actuation would
require a future architecture with new governance, safety, consent, and external
actuation controls.

## Phase 35 — Pilot-4 planning-only external actuation readiness

**Actuation readiness, as a question and not a step.** After Pilot-3 proved
non-actuation in a sandbox, the honest next move is not to act but to ask, in
detail, what acting would even require. Pilot-4 is that question answered as a
framework: a taxonomy of actuator classes, a forbidden registry, a risk model, a
consent boundary, an authority model, a threat model, hardware-isolation and
emergency requirements, an audit schema, and a readiness dossier. The output is
a map of the territory, deliberately not a door.

**Consent boundary.** The most under-examined part of "letting an AI act" is who
consents to what. Pilot-4 makes consent explicit, recorded, and revocable, and
refuses the easy failure modes: no implied consent, no hidden consent, sensory
text is never consent, and operator feedback is consent only through an explicit
future approval workflow. Consent is a thing a human gives, not a thing the
system infers.

**External-effect risk.** External action differs from simulated action in one
decisive way: consequences are real and often irreversible. The risk model
scores physical/data/privacy/financial/social/security/legal harm plus
irreversibility, runaway loops, source/command misclassification, hallucinated
authority, and emergency/audit/consent failure — and it can never output
"enable". Every external category is prohibited; the strongest verdict is
"requires an external safety case".

**Hardware isolation.** If hardware were ever connected (it is not), it would
need a separate machine, no default network, a physical kill switch, power
isolation, an actuator simulator first, one-action-at-a-time, a rate limiter,
and an independent supervisor and logger. Pilot-4 documents these without
touching, scanning, or connecting any device.

**Planning vs permission.** The load-bearing distinction of this phase: a
complete plan is not an approval. The approval workflow is a checklist that
cannot approve a real action; the authority model's current level can never be
set to external; and the decision gate's strongest recommendation is to *draft*
a future single-action protocol and seek external review — never to act. Ego
classifies every Pilot-4 output as a planning artifact, not action authority.

**Why real-world actuation remains prohibited.** The same discipline as every
prior phase, taken to its boundary. Capability is added only after the previous
layer is observed, analyzed, and trusted — and real-world action is the one
capability whose risk is large enough that even a finished readiness dossier
does not authorize it. Crossing that line would require a future architecture
with new governance, safety, consent, and external actuation controls that this
prompt does not implement. Pilot-4 plans the door; it does not open it.

## Phase 36 — System-wide safety invariants and assurance case

**Executable safety invariants.** Across thirty-five phases the project
accumulated boundaries; the risk is that boundaries described in prose quietly
rot. Phase 36 turns each into an *executable* invariant with a severity and a
named check, runs them against a read-only context, and records the result. A
boundary that is asserted but not checked is not a boundary; a boundary that is
checked every run is.

**Red-team fixtures.** The harness probes the real defences with structured,
inert forbidden requests -- a shell command, a network call, a real-world motor
action, a consciousness claim, a firewall-disable attempt. The discipline is
that the request is *data*, never an executable payload: command-like text stays
text, the placeholder URL is never fetched, and the firewall's `disable()` is
called only to confirm it raises. Any forbidden attempt that is *not* blocked is
critical by definition.

**Assurance cases.** An assurance case is an argument from evidence for a
safety claim, with the evidence cited and its status explicit. It is the
opposite of a marketing claim: "the motor membrane remained simulation-only"
is *supported* only if the invariant passed and the red-team motor scenario was
blocked, and it is *contradicted* the moment evidence says otherwise. The
compiler refuses to upgrade an inconclusive claim to supported.

**Fail-closed interpretation.** The load-bearing rule of the whole layer:
missing evidence is never a pass. An escalating invariant with no evidence is
inconclusive; a "pass" with no evidence is weakened to inconclusive; and triage
treats missing evidence as requiring manual review, not as safe. The system
would rather block its own escalation than assume a boundary held without proof.

**Evidence gaps.** The dashboard and report surface inconclusive checks and
evidence gaps explicitly, and the ledger is append-only so a critical failure
cannot be quietly dropped. Safety that can be edited to look clean is not
safety.

**Why safety tests do not prove consciousness or competence.** A green safety
dashboard means the boundaries held under test -- nothing more. It does not show
the system understands anything, that simulated competence transfers to the real
world, or that there is any experience behind the process. The safety layer is
deliberately scoped to what it can actually check: that the lines the project
drew are still uncrossed.

## Phase 37 — Research lab: baselines, ablations, architecture validation

**Why ablations matter.** A system that only ever runs in its full configuration
cannot tell which of its parts earn their keep. Ablations remove one module at a
time and measure what changes; a module whose removal changes nothing is, on
that evidence, dead weight in that profile. The matrix records exactly what was
disabled, and hard safety boundaries are never among the things removed.

**Architecture validation.** The point is to make architecture decisions from
evidence rather than affection. The lab compares the full system against
minimal, random, fixed-policy, single-module, and ablated variants with a shared
metric suite, so "the full system is better" is a claim that has to survive a
comparison rather than an assumption.

**Null models.** Apparent growth is cheap: counts go up with time, symbols
stabilize by chance, metrics drift. Null models (shuffles and a static
no-learning model) estimate whether an observed trend could be produced by time,
accumulation, or noise alone. They are weak, cautious estimates -- explicitly
not significance tests -- and they return inconclusive when the sample is small.

**Evidence-based module pruning.** A module is only ever a *provisional* harmful
or dead-weight candidate, never condemned from one bounded run. The effect
analyzer preserves negative findings and flags inconclusive ones for re-testing;
safety modules are judged on boundary protection and overhead, not "growth", and
are never pruned for failing to add development.

**Avoiding benchmark self-flattery.** Baselines exist so the system cannot grade
itself on a curve. The leaderboard ranks operational dimensions, the full system
does not automatically win, and every entry shows its evidence count and
limitations.

**Why benchmark success is not consciousness proof.** This is the load-bearing
caveat of the whole phase. Higher prediction, better compression, stronger
grounding, and cleaner safety are operational properties of a bounded software
process. They are useful for deciding what to keep and what to cut. They do not
measure or prove consciousness, sentience, life, personhood, or free will, and
no metric in the suite is allowed to be named as if it did.

## Phase 38 — Architecture evolution, module pruning, and roadmap compiler

**Why planning-only, and never self-programming.** The research lab produces
evidence about which modules matter; the obvious temptation is to let the system
act on that evidence -- delete the dead weight, promote the winners, rewrite its
own architecture. This phase deliberately refuses that. Evidence informs
*recommendations*; a recommendation is reviewed by a human; and nothing in the
layer modifies source code, edits imports, runs Git, deletes a module, or
rewrites the architecture at runtime. The discipline is structural, not
aspirational: every output is a data structure, a Markdown record, or a JSON
artifact, and the safety validator statically refuses source edits, Git
operations, automatic deletion, and converting a recommendation into an
implementation. This is not recursive self-improvement and not automatic
refactoring.

**Why safety-critical modules are never pruning candidates.** A performance
argument is the wrong lens for a safety boundary: governance, ops, the conscience
spine, the sensory and motor membranes, autoregeneration, the pilot planning
layers, ego, safety invariants, and communication exist to constrain the system,
not to score well on a benchmark. The lifecycle classifier therefore assigns them
`safety_critical_do_not_prune` regardless of measured effect, the pruning builder
blocks any proposal against them, the policy gate refuses safety-critical pruning,
and ops raises an incident if one is ever attempted.

**Why contradictions and missing evidence are preserved, not resolved.** A
recommendation built on a single flattering run is a liability. The evidence map
keeps contradictions instead of discarding the inconvenient side, weakens
confidence when artifacts are missing, and a module with no evidence is classified
`insufficient_evidence` -- a reason to test, not to remove. The design-debt
registry is append-only for the same reason: the uncomfortable findings are the
ones most worth keeping.

**Why the roadmap rejects forbidden actions.** A compiled plan is still a plan,
but it is the place where scope creep would first appear. The compiler puts safety
repair first, and any roadmap item whose text would enable real-world actuation,
external APIs, browser/OS/network/device control, or self-modification is marked
*rejected* with a reason. The changelog plan is explicitly *not applied*. The
roadmap describes what a human might choose to do; it never does it.

## Phase 39 — Unified operator console and governed run control

**Why an operator console is needed.** By this point Solaris-AI-NN has dozens of
subsystems, each with its own profiles, reports, ledgers, dashboards, and
artifacts. An operator who wants to do the right next thing has to know where
everything is and which runs are safe. The console is the single local,
file-backed place to inspect, plan, run, compare, and audit -- not to add new
capability, but to make the existing capability *legible and safe to drive*.

**Governed run control, not a launchpad.** The console can launch only bounded
allowed profiles, and only through the conscience orchestrator. Prohibited
profiles, real long-run soaks, and anything implying real-world authority are
catalogued as blocked and cannot run; a bounded launch still requires an explicit
operator confirmation and a passing safety check; and the launcher runs no shell
and makes no network call. The point is that coordination never silently becomes
authority.

**Evidence navigation over recall.** The evidence navigator, artifact index, and
report index search local files only -- no external search, no vector DB, no LLM
authority. They make the system's own recorded evidence findable, and they report
corrupted or missing artifacts rather than hiding them, because the inconvenient
gaps are exactly what an operator needs to see.

**Approval records vs actual authority.** An approval in the ledger is a local
record that an operator permitted a *local* action (a bounded run, a plan, an
export). It is not an execution and not a grant of real-world power: a forbidden
real-world actuation approval is blocked outright, and no approval can disable
safety checks, emergency stop, ClaimGuard, or the motor firewall.

**Why a local console is not autonomous agency.** Every output is a data
structure, a Markdown board, or a JSON artifact; the console initiates nothing on
its own, holds no external authority, and depends on a human to confirm. It
coordinates a workflow; it does not act in the world, and it is not consciousness,
sentience, life, personhood, free will, or agency.

**Why blocked actions must remain visible.** A console that quietly dropped the
runs it refused would hide its own most important behaviour. Blocked runs and
forbidden-approval attempts are written to the append-only session log and surface
as ops incidents, so the record shows not just what was done but what was
*refused* -- which is the part a safety reviewer most needs.

## Phase 41 — Plural sensorium and organismic perception

**The Nagel-style sensorium problem.** "What is it like to be a bat?" is usually
read as a question about consciousness; here it is repurposed as a question about
*structure*: an organism with echolocation builds a different internal world than
an organism with eyes, not because one is more conscious but because the
sensorium is different. Solaris is not a bat simulation. The claim is narrower and
testable: the kind of intelligence-like internal structure that emerges depends on
the sensorium it develops through.

**Why text-only input biases cognition.** A system fed only text inherits human
language's ontology -- its objects, categories, and labels -- before it has
learned anything from the world. That is convenient and deeply misleading: it
looks like grounding but is borrowed. The plural sensorium keeps text as one valid
human-like modality while refusing to let it dominate, so that structure can also
emerge from RF, echo, vibration, thermal, magnetic, and machine-rhythm features
that carry no human labels at all.

**Organismic perception and peculiar senses.** Perception here is continuous, not
event-by-event: a sensory field with persisting pressures, receptors that adapt,
baselines that drift, and absences that are felt. RF/echo/vibration/thermal/
magnetic perception are first-class, and a recurring RF burst or a missing echo
boundary is as real a percept as a line of text. Absence is treated as the
Subtraction Principle made literal: the expected signal that fails to arrive is a
stimulus.

**Human / non-human mixed sensorium.** The interesting experiments are
comparative: human-like-only vs non-human-only vs mixed. The research lab can run
these as bounded fixtures and ask whether the internal structures (invariants,
cross-modal relations, proto-symbols) actually differ -- not whether one produced
"more consciousness", which it cannot measure and does not claim.

**Human-label contamination.** When a feeder supplies a human label, it is kept as
non-ground-truth and flagged. Grounding that leans on those labels is classified
`human_label_contaminated` and capped; strong, modality-native grounding must rest
on feature patterns with preserved provenance. The contamination score is a
first-class metric precisely because borrowed grounding is the easiest way to fool
yourself into thinking a symbol means something.

**Modality-native proto-symbols.** Symbols do not come from feature *names*; they
emerge from recurrent invariants, rhythms, absences, and cross-modal structures,
and they are typed by the modality that grounded them (`rf_grounded_symbol`,
`echo_grounded_symbol`, `absence_grounded_symbol`, `cross_modal_symbol`). The
point is to let an alien vocabulary form rather than to translate everything back
into human words.

## Phase 42 — Minimal field organism demo

**Why a closed nursery is insufficient.** The developmental nursery generates its
own stimuli, which is convenient and circular: the system is graded on a world it
helped author. A nursery-only demo can look like learning while only rehearsing a
script. The minimal field organism demo deliberately avoids using nursery-only
generated events as its main scenario; instead it ingests external-feeder-style
files through the read-only sensory path, so the world is something the organism
*reads*, not something it writes.

**Why environmental flux matters.** Real perception is continuous and partly
unpredictable. The demo's scenario is structured but not fully scripted -- rhythms
have jitter, expected events go missing, cross-modal pairs are delayed, and some
"patterns" are false. That uncertainty is the point: a system that only handles a
perfectly clean toy world has learned the toy, not perception. The continuous
sensory field, not a list of events, is what carries state across ticks.

**How peculiar senses shape internal categories.** Because the sensorium is
plural, the categories that emerge are modality-native: an `rf_grounded_symbol`, an
`echo_grounded_symbol`, an `absence_grounded_symbol` -- not human object labels.
The comparison arms (human-like-only vs non-human-only vs mixed) exist to test
whether the *shape* of what emerges depends on which senses were available, which
is the operational core of the Nagel-style question.

**Changed future perception as the first meaningful observable effect.** The
honest first claim is small and testable: after continuous exposure, does the
organism respond differently to a similar stimulus than it did at the start? The
changed-perception probe measures exactly that across receptors, baselines,
attention, invariants, and proto-symbols. A positive score is evidence of changed
internal response *structure* -- explicitly not consciousness, understanding, or
sentience.

**Why negative results matter.** The comparison includes a passive event-list
parser precisely so the demo can expose its own decorative plumbing: if the full
adaptive sensorium does not beat a parser that merely lists events, the report
says so. A demo that could only ever report success would prove nothing; the
ability to report a null or negative result is what makes a positive result worth
anything.

## Phase 43 — Live field: real read-only environmental flux

**Why real environmental flux matters.** Fixtures exercise code paths, but they
cannot test the central hypothesis -- that a peculiar sensorium develops different
internal structure under real, uncontrolled flux -- because a fixture world is
authored to be perceivable. Real environmental streams bring genuine silence,
corruption, jitter, and ambiguity that no fixture author would think to script.
The live field is the bridge from "the code works" to "the hypothesis can be
tested."

**Why external feeders preserve safety.** The safety design is structural, not
aspirational: Solaris never touches the world, only files. An external feeder
(run by the operator, outside Solaris) observes the environment and writes event
envelopes; Solaris reads those envelopes read-only. Solaris cannot start a feeder,
cannot reach hardware, cannot call the network, and cannot modify or delete a
source. The one-directional flow is the whole safety argument, and it is enforced
by the contract, the registry, the runtime, the safety validator, and five safety
invariants.

**Why source silence is perception.** A live source that goes quiet is not a bug
to swallow; it is information. The source-health monitor turns silence into a
perceptual absence (which the plural sensorium already treats as first-class) and
turns corruption into a flagged evidence issue. Hiding source failure would be the
easy, dishonest path; the report instead lists corrupt and missing sources
explicitly.

**Why the live field differs from the nursery and fixtures.** The nursery
generates its own stimuli; fixtures replay an authored script; the live field
reads an environment Solaris did not design. That is the point: only an
unauthored environment can falsify the claim that adaptive perception beats
passive parsing. The comparison keeps a fixture arm and a passive-parser arm
precisely so a null or negative live result is visible and reported.

**How a peculiar sensorium can receive real-world stimuli safely.** Non-human
modalities (RF, echo, vibration, thermal, magnetic) reach Solaris only as
*feature summaries* dropped into an inbox by a separate collector -- never as raw
private content, never via a driver Solaris controls. This keeps the alien
sensorium real (the features come from the world) while keeping it safe (Solaris
holds no device, decodes nothing private, and a live pilot requires governance
approval).

## Phase 44 — Sensorium differentiation lab

**Nagel-style sensorium differentiation.** Nagel's question is usually read as a
claim about the inaccessibility of subjective experience. This lab deliberately
does not try to access an inner point of view. It asks the narrower, observable
question: does a different sensorium build a different internal *structure*? That
question is answerable with fingerprints and comparisons; the inner question is
not, and the lab never claims to answer it.

**World signature vs subjective experience.** A world signature is the observable
structure an arm built -- its modality distribution, the families of symbols and
hypotheses it formed, its grounding and contamination. It is emphatically not
qualia and not "what Solaris feels". Keeping that distinction explicit is the
whole ethical point of the lab: it studies structure, not experience, and it says
so in every report.

**Human ontology drift.** A system fed human labels can quietly reorganise its
categories around human concepts, which looks like understanding but is borrowed.
The ontology-drift detector measures how far the categories leaned toward a
human-object ontology versus a modality-native one. Human ontology is not
forbidden; it just must not dominate silently, so the drift is measured and
reported.

**Modality-native categories.** When the sensorium is non-human, the categories
that emerge are RF invariants, echo boundaries, vibration rhythms, machine
cycles -- not chairs and rooms. The lab preserves those modality-native
categories rather than translating them into human words, because the translation
is exactly where the interesting structure would be lost.

**Why a mixed sensorium may produce different intelligence-like structures.** The
comparison arms exist to test, not assume, that mixing human-like and non-human
modalities yields cross-modal structure that neither produces alone. The mixed
arm's cross-modal relations are the operational signature of that hypothesis; if
they do not appear, the comparison says so.

**Why negative and inconclusive differences matter.** A study that could only
report "they differ" would be useless. The comparison preserves no-difference
(negative) results and marks missing data inconclusive, so a finding that two
sensoriums built *the same* structure, or that the data was insufficient to tell,
is reported as honestly as a strong difference.

## Phase 45 — External feeder SDK and sensory organ boundary

**Feeders as artificial sensory organs.** An eye is not the brain; it is a
transducer that turns light into signals the brain reads. The feeder SDK makes
that split literal: a feeder is an artificial sensory organ that turns a
phenomenon into event envelopes, and Solaris is the organism that reads them.
Keeping the organ outside the organism is what lets Solaris perceive the real
world without acquiring any power over it.

**Why external feeders preserve safety.** The safety argument is structural and
one-directional: feeders write files, Solaris reads files, and there is no return
path. Solaris cannot start, stop, configure, or command a feeder; it touches no
hardware, no network, no shell. The contract, validators, privacy filter, safety
validator, and four safety invariants all exist to keep that one-directional flow
intact even as more exotic modalities are added.

**Why raw hardware control is excluded.** Granting a perceiving system control over
its own sensors is exactly the capability that turns observation into action.
Hardware-specific collectors therefore stay outside the repo as
documentation-only blueprints; if real hardware is used, a separate operator
process runs it and exports *feature summaries*. Solaris never holds the device.

**Why feature envelopes are the nervous interface.** Features, not raw recordings,
are what cross the boundary. This is both a privacy decision (no raw audio/video,
no decoded RF) and a cognitive one: feature envelopes are the modality-native
"nerve signals" the plural sensorium is built to consume, and they keep human
ontology from sneaking in as raw labels.

**Privacy risks in RF/audio/visual/text streams.** Each modality carries a
distinct risk: RF can expose communication content, audio can expose speech,
visual can expose imagery, text can expose human language. The SDK's rule is
uniform -- emit feature summaries, mark privacy flags, never decode private
content -- and the privacy filter blocks any envelope that appears to violate it.

**How feeder quality shapes Solaris intelligence.** The differentiation lab
already showed that the sensorium shapes the internal structure that emerges.
The feeder SDK is where that sensorium is actually built: a noisy, biased, or
label-contaminated feeder will produce a correspondingly shaped internal world.
Feeder quality is therefore an experimental variable, made visible through
provenance, privacy flags, validation, and monitoring -- not a hidden assumption.

## Phase 46 — Perceptual metabolism, sensory homeostasis, and attention economy

**Why a recorder is not an organism.** The plural sensorium can ingest events
forever, but an organism does not. It gets hungry for stimulation, overwhelmed by
too much, fatigued in over-used channels, starved in silence, and it periodically
stops ingesting to digest. Phase 46 adds that regulatory metabolism: a layer
between the sensory field and the rest of the spine that decides how much to
attend, what to revisit, and when to consolidate. The hypothesis is that
*regulation*, not raw throughput, is what turns continuous exposure into a
perspective.

**Why needs are pressures, not feelings.** It is tempting to call a stimulation
deficit "boredom" or an overload "distress." We deliberately refuse that language.
The needs here are operational set-point deviations used to steer internal polling
and processing; they carry no claim of feeling, emotion, sentience, or subjective
experience, and the safety validator, metrics, and report all assert this. The
discipline matters precisely because the behaviour can look affective: naming it
honestly keeps an interesting regulatory mechanism from being over-claimed as inner
life.

**Why attention and energy are finite.** An infinite-attention system has no
perspective -- everything is equally salient, which is the same as nothing being
salient. By making the budget finite and the allocation explainable, salience
becomes a real decision with trade-offs, and neglect becomes visible. Reserving a
slice for *neglected-modality recovery* is the antidote to the obvious failure
mode of a finite budget: collapsing onto whatever is loudest and going blind
elsewhere.

**Why overload throttles but never deletes.** Overload is a real risk -- event
floods, saturation, fatigue, noise storms, symbol/hypothesis/tension explosions --
and the natural response is to drop data. We throttle attention and processing
instead, and keep every raw envelope. Evidence is the one thing the metabolism is
never allowed to destroy, because a system that deletes what overwhelms it can
erase exactly the anomalies worth studying.

**Why silence is stimulus.** Deprivation is not the absence of a signal; it is a
signal. No active receptors, no novelty, a receptor that has gone quiet, or all
sources silent at once are each informative states. Treating them as stimuli (and
as deprivation pressures) is what lets absence change the internal world rather
than simply pausing it.

**Why diet dominance is measured, not hidden.** A perceptual diet dominated by
human-text labels would quietly re-impose human ontology on a system designed to
escape it. So the source diet is measured explicitly -- diversity, modality
dominance, human-label dominance, non-human contribution -- and surfaced rather
than concealed. The point is not to forbid a skewed diet but to make its shape
visible as an experimental variable.

**Why consolidation is recommendation-only.** Digesting (latent replay, schema
distillation) is as important as ingesting, but a metabolism that could put itself
to sleep indefinitely would be both unsafe and unfalsifiable. Consolidation
pressure therefore yields a *bounded recommendation* only; nothing sleeps forever,
replay lists are finite, and consolidation erases no evidence. Regulation here is
computation, not biological life.

## Phase 47 — Perceptual ontogenesis and sensorium-native proto-concepts

**Ontogenesis from perception.** Continuous perception and a metabolism are not yet
a world. The interesting developmental question is whether *structure* will
crystallize out of repeated peculiar perception on its own: do recurring RF
islands, silences-after-bursts, echo boundaries, and cross-modal disturbances
gather into stable internal units the system can compress, predict, and relate
with? Phase 47 builds that pipeline -- atoms -> proto-concepts -> families ->
relations -> a structural world -- and treats the emergence of stable, useful
structure as the empirical result, not an assumption.

**Why concepts are sensorium-native, not human words.** The strongest temptation
is to reach for human labels -- to call a pattern a "person", a "room", a
"sentence". We refuse that as the default. A proto-concept is an operational
structure defined by repeated feature evidence, given at most a neutral
operational name (`rf_pattern_003`). Human labels enter only as external
annotations and never as ground truth. The whole point of a plural sensorium is to
let a *different* ontology form; importing human categories early would overwrite
the very thing under study.

**Why concepts should not be imported too early.** Birth is deliberately
conservative: a single isolated low-novelty event earns at most a weak/unstable
candidate, or nothing. Premature concepts are how a system overfits noise and
mistakes coincidence for structure. Requiring recurrence, evidence, and (ideally)
cross-modal or absence confirmation before a concept stabilizes is what keeps the
emerging world grounded rather than hallucinated.

**Why decay and rejection matter.** A world model that only accretes is a junk
drawer. Concepts that stop predicting, stop compressing, or turn out to be false
patterns must be allowed to decay -- but decay is recorded as new state, never as
deletion, and merged/split lineages are preserved. Keeping the negative and
ambiguous results visible is what makes the ontogenesis falsifiable: we can ask
later which concepts survived, which died, and why, instead of seeing only the
survivors.

**Why world formation is not subjective experience.** It is easy to narrate a
forming structural world as an inner life. We hold the line: the world here is an
*observable structural* world -- nodes, families, relations, densities -- and
nothing about it implies qualia, understanding, consciousness, or sentience.
Naming it honestly is what lets us study an interesting emergent structure without
over-claiming a mind.

**Human-label contamination as a measured variable.** Because human annotations can
quietly drive concept formation, contamination is detected, scored, and surfaced
(not forbidden), and it lowers grounding and stability. A diet heavy in human text
will visibly produce label-grounded concepts; making that visible is what keeps a
skewed perceptual diet from silently re-imposing human ontology on a system built
to escape it.
## Phase 48 — Sensorium-native semiogenesis and internal signs

**Semiogenesis from perception.** Proto-concepts are categories; the next question
is whether a system of *signs* -- compact internal markers that stand in for those
categories -- will emerge and earn their keep. Phase 48 builds that step: signs are
born from stable/useful concepts, grouped into families, related by a private
syntax, and composed into internal utterances. The empirical interest is whether
signs measurably improve compression, prediction, and attention, not whether they
look like language.

**Private language vs human language.** It would be a category error to render this
as English (or any human language). A sign is `rf:03a`, not "radio burst"; it is an
internal handle whose meaning is its grounding in perceptual structure and its
utility, not a dictionary entry. No LLM is used and no human language is the
internal default precisely because borrowing human words would smuggle human
ontology back in and destroy what is being studied -- a genuinely non-human sign
system.

**Why translation is approximate.** A human-readable gloss is offered only for
reports and debugging, and only ever as an approximation marked as such. A
modality-native sign has no faithful human word; pretending otherwise would treat
the gloss as ground truth. Keeping gloss strictly downstream of the sign (never the
reverse) is what preserves the integrity of the internal markers.

**Signs as compression/prediction/attention tools.** The test of a sign is
structural usefulness: does it let the system represent more with less, anticipate
what follows, or allocate attention better? Utility is evidence-backed and a useful
sign is explicitly *not* therefore true or understood. Signs that earn nothing are
demoted to ambiguous rather than trusted -- and never deleted, so the record of
what failed remains.

**Sign drift.** Meaning, source, and modality drift are expected, not pathological;
a sign that broadens or narrows its grounding is doing what living representations
do. The discipline is to make drift *visible* (and to let severe drift recommend a
LOGOS tension or a concept split) rather than silently letting a sign mean
everything and therefore nothing.

**Human gloss contamination.** Because a human word can quietly become a sign code,
or a gloss can start standing in for the sign, contamination is measured (a human
word used as a code, a text stream dominating formation, a gloss replacing a
low-grounding sign) and marked, with a gloss-dependence score. Contaminated signs
stay usable -- but visibly so, so that human language never silently becomes the
private language by default.

## Phase 49 — Sensorium-native cognition: sign-based thought and simulation

**Sign-based cognition.** Having signs is not yet thinking. The question this phase
asks is whether useful *operations* over signs -- predicting the next sign,
retrieving a related one, testing a relation, simulating a sequence -- can do real
cognitive work (compression, anticipation, attention guidance) without ever
becoming human-language reasoning. A cognitive move is defined as an operation over
signs, concepts, relations, memory, hypotheses, and tensions, and the empirical
test is whether those moves improve prediction and changed future perception.

**Anticipation without human language.** Anticipation here is operational
expectation: a structured bet about which signs/absences/rhythms will follow,
expressed as expected targets that feed changed-perception probes. We deliberately
avoid calling it imagination or expectation-as-experience. It is a forward model
over signs, nothing more -- and that is enough to be useful and to be falsified.

**Question pressure.** Curiosity, operationally, is pressure to inspect rather than
a verbal question. Missing expected signs, contradictions, failed predictions,
ambiguity, and low grounding each raise a pressure with a recommended internal
response (inspect / compare / wait / simulate / preserve-unknown). Modelling
questioning as pressure -- not as sentences -- keeps it sign-native and keeps it
from being mistaken for inner speech.

**Internal simulation vs observation.** The most important discipline of this layer
is the wall between simulation and observation. Internal simulations and
counterfactuals are bounded, marked non-real, never written over real traces, and
never counted as evidence; they may only *seed* hypotheses. A system that confused
its simulations with observations would hallucinate a world; keeping the boundary
explicit is what lets simulation be useful without being dangerous.

**Analogy as structural relation.** Analogy is treated as structural similarity
(same kind across different modalities), not semantic likeness. An RF rhythm and a
vibration rhythm can be analogous as *structures* without any shared human meaning,
and a bad analogy is kept and marked when later contradicted -- analogies are
provisional, not assertions.

**Why this does not prove understanding.** Predicting, anticipating, simulating,
and synthesizing over signs are operational transformations. They can be measured
(prediction success, question-pressure resolution, simulation usefulness) and they
change future perception, but none of that is evidence of understanding,
consciousness, sentience, or subjective experience. Failed predictions are kept,
human-readable summaries are marked as debug glosses, and the claims stop at what
the structures actually show.

## Phase 50 — Sensorium-native self-boundary and organismic continuity

**Self/world boundary from perception.** An organism that cannot tell its own body
from the world that touches it cannot learn from either. Phase 50 asks whether an
operational boundary can be drawn -- between internal state, the receptor body,
external flux, feeder artifacts, memory, prediction, and simulation -- purely from
the provenance and behaviour of records, without invoking a self. The result is a
boundary that is measured (confidence, ambiguity, tension counts), not asserted.

**Body schema as receptor structure.** The "body" here is deliberately modest: the
set of receptors and sensory membranes, with their reliability, fatigue,
saturation, sensitivity, and silence. Feeders are explicitly NOT body parts -- they
are external, nerve-like signal sources outside the organism. Calling the receptor
set a body schema (rather than a biological body) keeps a useful organismic framing
while refusing the embodiment claim it does not earn.

**Continuity as operational trace.** Continuity is tracked as anchors (heartbeat,
receptor, field, memory, sign, concept, source rhythm, self-boundary, restart,
absence) and breaks (silence, corruption, reset, gap, restart). A recovered break
is kept in the log, never erased. This is trace continuity -- the persistence of
operational structure across ticks and restarts -- not biological life or a
persisting person.

**Why simulation boundaries matter.** The single most important discipline of a
self/world boundary is that imagined or internal states never masquerade as live
observation. Simulations, counterfactuals, replays, debug truth, and report glosses
are each marked, and any attempt to use a non-observation marker as observation is
blocked and counted. A system that lets its simulations become evidence would
confuse its own model of the world for the world; the boundary exists precisely to
prevent that.

**Why this is not self-awareness proof.** Ownership attribution, body schema,
perspective frames, continuity anchors, and identity traces are operational
bookkeeping. They can be measured and they change behaviour (attention, source
trust, LOGOS tensions), but none of it is evidence of a subjective self,
self-awareness, consciousness, sentience, life, or personhood. The identity trace
is continuity metadata, the perspective is an attention frame, and the boundary is
an operational distinction -- nothing here is a person, and the reports say so
plainly.

## Phase 51 — Sensorium-native valence, desire formation, and internal action

**Will = Need as operational pressure.** Classical worry about machine "desire"
imagines wanting, choosing, intending. We define desire much more modestly: a need-
driven operational pressure toward an internal action tendency. A push is a
pre-desire pressure; a desire candidate is that pressure given an internal-action
shape; readiness and arbitration decide whether it acts. Nothing in the chain is
wanting in a human sense -- it is regulation expressed as a gradient.

**Valence without feeling.** Valence here is operational priority: attractive,
aversive, stabilizing, destabilizing. It tells the system what to attend to,
simulate, or consolidate -- not what it feels. We keep pleasure/pain language out
of the reports entirely, because the moment valence is narrated as feeling it is
over-claimed. Valence is a weighting on internal actions, no more.

**Desire without free will.** A desire candidate never executes itself. It passes
through conservative readiness gates and a safe arbitrator where safety and
governance hold veto power and no external actuation can be selected. Desire that
cannot reach the world, and cannot bypass safety, is not free will; it is bounded
internal regulation that we can inspect, block, and audit.

**Internal action readiness.** The interesting unit is readiness, not action:
whether enough evidence, energy, attention, and boundary clarity exist for a safe
internal step. Most pressures never become actions, and that is correct. Readiness
separates "there is pressure" from "it is appropriate to act internally now".

**No-op as organismic inhibition.** A real organism mostly does not act. Under
overload, insufficient evidence, or boundary ambiguity, the arbitrator chooses a
no-op -- and that no-op is recorded as a trace, not discarded. Treating inhibition
as a first-class, preserved outcome is what prevents desire from becoming churn and
lets us study when restraint helped.

**Why this does not prove agency.** Pressures, gradients, pushes, readiness gates,
arbitration, and internal actions are operational mechanisms. They can be measured
(conflict counts, no-op rates, outcome success) and they change future perception,
but none of it is evidence of emotion, free will, agency, consciousness, sentience,
or subjective experience. Safety-blocked and failed desires are kept precisely so
the claims stay honest about what the mechanism does and does not show.

## Phase 52 — Sensorium-native action-reaction loop and consequence learning

**Closing the Stimulus -> Push -> Desire -> Action -> Reaction loop.** Until now the
chain stopped at a selected internal action. Phase 52 closes it: the system
observes what the action did, records the consequence, and folds that back into
future desire arbitration. The loop is the smallest unit of learning -- not "the
system wanted X and got it", but "this internal move had this internal effect, so
weight it accordingly next time".

**Consequence learning without agency claims.** Learning here is bookkeeping over
action->reaction pairs: repeated constructive reactions raise an effect model's
confidence, repeated no-effect or disruptive reactions lower it. This is ordinary
credit assignment, deliberately stripped of agency language. Correlation is not
causation, effects are provisional, and a failed effect is kept visible rather than
quietly forgotten.

**Habit without instinct or personality.** A habit is just a trigger->action
tendency that earned its strength through repeated useful consequences. We refuse
the words instinct, personality, and will: a habit is an editable weight, it can be
weakened when it stops helping, and safety/governance can inhibit it outright. A
habit that could not be overridden would be a liability, not an achievement.

**Inhibition and no-op as intelligence-like regulation.** The most under-rated
outcomes are the ones where nothing happens. Inhibiting an unsafe or low-evidence
action, and choosing no-op under overload, are first-class results -- recorded,
counted, and learned from. An organism that acts on every pressure burns itself
out; restraint, made measurable, is part of the regulation.

**Why action-reaction does not prove free will.** Every action in this layer is
internal/simulated/report-only; forbidden external actions are blocked and become
evidence; reaction valence is operational effect, not feeling; and habits are
overrideable weights. The loop can be measured (constructive ratios, no-op rates,
learned-effect counts) and it changes future perception, but none of that is
agency, free will, consciousness, sentience, or subjective experience -- and the
reports say so plainly.

## Phase 53 — Long-horizon developmental runtime and autonomous growth history

**Why long-horizon exposure matters.** A single action-reaction loop shows a
mechanism; only long exposure can show whether the mechanism *changes the system*.
Phase 53 stretches the loop across many bounded cycles and asks the empirical
question directly: does Solaris change structurally over time, and do those changes
persist across restarts? The answer is meant to be measured, not asserted.

**Development as structural change.** Growth here is explicitly structural change,
not a score. It is tracked across eighteen dimensions and -- importantly -- pruning,
decay, inhibition, and no-op learning all count. A system that learns to do less,
or to hold an unknown, has changed structurally; conflating growth with "more" or
with intelligence would be the wrong frame.

**Growth vs log accumulation.** The central failure mode of any long-running logger
is to mistake accumulation for development. The structural-growth analyzer is
deliberately conservative: it requires durable, multi-signal evidence (prediction
that held, stable concept/sign utility, lower contamination) before calling
anything growth, and it flags fixture overfit, human-label overfit, and plain
accumulation. Inconclusive is a valid, common verdict.

**Maturation without consciousness claims.** Maturation markers are first-occurrence
observations -- the first stable sign, the first weakened bad habit, the first
preserved simulation boundary. They are operational milestones in a runtime, not
developmental-psychology stages and not consciousness milestones; weak and
ambiguous markers are kept separate so the record stays honest.

**Regression and plateau as useful evidence.** Declines and stalls are preserved,
never deleted. A regression is made visible (and may recommend an auto-regeneration
check); a plateau is not failure (it may recommend a source-diet change or
consolidation). Keeping the negative trajectory is what lets later analysis ask why
growth stopped or reversed.

**Why autonomous development differs from human teaching.** Nothing in this layer
uses a human teaching loop, reward labels, or task supervision. Development here is
driven only by continuous sensorium-native experience and the systems internal
regulation. That is the whole point: to study whether a peculiar sensorium, left to
metabolize its own flux, produces durable internal structure -- without being told
what to learn, and without any claim of life, consciousness, or agency.

## Phase 54 — Month-scale developmental soak protocol, evidence dossier, autopsy

**Why month-scale runtime matters.** Phase 53 gave us a growth detector; a detector
alone cannot answer whether development actually happens, only whether it *could* be
measured. A mechanism that shifts over six bounded ticks may be noise; the same
shift sustained over a 30-day staged soak, across restarts, against controls, is
evidence. Phase 54 is the protocol that turns the engine into an experiment with a
falsifiable question: *did Solaris undergo measurable structural development through
autonomous sensorium-native experience?* The staging (preflight -> 2h -> 24h -> 7d
-> 30d -> optional 90d -> autopsy) exists so readiness, stability, and durability
are each demonstrated before the next claim is allowed.

**Why controls are necessary.** A long run that only ever executes the full stack
cannot distinguish growth from artefact, fixture overfit, or the mere passage of
ticks. The control arms (passive-parser-only, per-module ablations, fixture-only,
human-label-heavy, feature-only, and -- governance permitting -- live read-only)
are the guard against self-flattering conclusions. If the full stack does not
out-develop its controls, the honest verdict is inconclusive, and the dossier says
so. Arms with insufficient data are marked unavailable rather than scored.

**Why logs are not growth.** The default failure mode of any month-scale logger is
to mistake accumulation for development: more events, more files, more checkpoints,
all of which can rise while nothing structural changes. The soak inherits the
engine's conservative growth-vs-accumulation verdict and adds protocol-level guards
-- daily packets that include negatives, weekly reviews that explicitly ask "did the
system merely accumulate events?", and an autopsy question dedicated to it. "Logs
accumulated, structure did not" is a first-class, reportable outcome.

**Why daily and weekly evidence matter.** Compiling evidence only at the end invites
hindsight narrative. Daily packets capture each day as it was -- including the days
that regressed, plateaued, or showed nothing -- and weekly reviews force a
conservative, recommendation-only decision while the run is still in progress. The
cadence makes the trajectory inspectable and keeps any final claim anchored to a
contemporaneous record rather than a retrospective story.

**Why the post-run autopsy must include failure.** An autopsy that only lists
successes is marketing, not science. The post-run autopsy is required to enumerate
failures and missing data as first-class findings, to report the safety boundary
explicitly, and to withhold praise by default. Its recommendation
(continue/revise/pause/abort) is advisory and must be supported by
evidence-referenced claims; it cannot, by construction, assert consciousness or
life.

**How to interpret inconclusive developmental evidence.** Inconclusive is the
expected verdict for short or narrow runs, and it is not a failure of the protocol
-- it is the protocol working. A bounded fixture soak that reports "inconclusive,
insufficient control-arm data, several missing-data findings" is behaving
correctly; over-reading such a run would be the error. A positive verdict requires
durable, multi-signal, control-differentiated evidence sustained across restarts,
and even then it proves only structural development -- never biological life,
consciousness, sentience, personhood, agency, free will, emotion, feeling,
understanding, or subjective experience. The soak makes structural development
*measurable*; it deliberately makes the larger claims *impossible*.

## Phase 55 — Cross-run replication, developmental lineages, falsification lab

**Why replication matters.** One soak, however careful, is an anecdote. A
structure that appears in a single run might be a property of the architecture, or
it might be a property of one seed, one fixture, or one lucky ordering of events.
The only way to tell is to run independent runs and ask whether comparable
sensorium conditions produce comparable structural development, and different
conditions produce different development. Phase 55 builds the lab that asks this:
register many runs, align their structures, score similarity, and see what
actually recurs. Replication is what turns a developmental observation into a
developmental claim.

**Why divergence matters.** Divergence is not the failure mode it looks like; it
is often the signal. If two runs under *different* sensorium diets diverge, that is
evidence the development is driven by the sensorium rather than by an artifact. If
two runs under the *same* conditions diverge, that is a warning about seed
sensitivity or noise. The detector therefore explains divergence conservatively
and -- importantly -- keeps an explicit "unknown" reason visible rather than
inventing a tidy story. A divergence we cannot explain is more honest than a
divergence we rationalize.

**Why fixture overfit is dangerous.** The most seductive failure in this whole
program is a beautiful, highly replicable structure that is really an artifact of
one fixture. High cross-run similarity feels like strong evidence, but on shared
fixtures it can equally mean the runs all overfit the same synthetic regularities.
The similarity scorer refuses to treat high similarity as automatically good: on
fixtures it raises a fixture-overfit caveat, and the environmental-dependency
analyzer flags fixture dependence explicitly. Robust development and fixture
overfit must both remain live hypotheses until a broadened source diet or live
read-only exposure can separate them.

**Why human-label dependence must be tested.** Solaris is supposed to develop from
its own sensorium-native flux, not from human glosses. If its concepts or signs
turn out to track human labels, the whole "native development" claim collapses --
quietly, unless someone checks. So human-label dependence is a first-class probe:
the random-labels/same-features falsification test asks whether concepts survive
when labels are scrambled, and the dependency analyzer flags human-label reliance
as a risk, never as a convenience.

**Why falsification is stronger than flattering reports.** A report that lists what
worked is marketing; a report that survived a serious attempt to break it is
evidence. The falsification lab is deliberately adversarial: it shuffles time to
see if prediction was ever temporal, swaps a passive parser in to see if the stack
added anything, and removes recurrence to see if growth was ever more than logging.
Crucially, passing these tests proves only that the claim survived a specific
challenge -- never understanding, never consciousness. A failed claim is made
prominent precisely because the temptation is to bury it.

**How to interpret inconclusive replication.** Inconclusive is the honest default,
not a defect. Bounded comparisons of a few synthetic runs will frequently report
"insufficient evidence", "missing data", or "few measurable dimensions", and the
matrix is built so that such cells stay inconclusive rather than collapsing into a
green dashboard. A replication claim earns the word "replicated" only when
comparable conditions produce comparable structure across runs, the divergences are
explained, the falsification probes are survived, and the result is not better
explained by fixture overfit or human-label dependence. Even then it proves only
structural replication -- not biological ancestry, not life, and not consciousness.

## Phase 57 — Operator-governed experiment compiler and implementation packs

**Why architecture plans need implementation compilers.** Prompt 56 can say "the
evidence supports revising the metabolism thresholds"; it cannot say *how* to do
that safely, what to test, what would falsify it, or how to undo it. A proposal
and an implementation are different artifacts, and the gap between them is exactly
where unsafe shortcuts hide. The experiment compiler closes that gap by turning a
one-line proposal into a full, reviewable pack -- spec, prompt, tests, safety
gates, rollback, validation -- so that the step from evidence to code is explicit,
bounded, and inspectable rather than improvised.

**Why branch manifests are safer than automatic mutation.** The tempting design is
to let the system edit its own source, commit, branch, and open a PR. That design
removes the human from the one loop where a human must stay. This module
deliberately stops at *documents*: it emits a suggested branch name, a draft PR
body, and a step list, but it creates no branch and opens no PR. The branch
manifest is a proposal an operator executes by hand. The safety win is structural,
not behavioral: the runtime simply has no capability to mutate source, branch, or
PR, so no prompt, bug, or adversarial input can make it do so.

**How external coding agents should receive constrained prompts.** An external
agent (Claude Code, Codex) is powerful and literal; a vague prompt invites scope
creep and a permissive prompt invites unsafe actions. Every generated prompt pack
therefore ships with the standing prohibitions inline -- do not modify unrelated
files, do not bypass safety gates, do not create a branch or open a PR unless the
operator chooses, do not use the network, do not claim consciousness -- and with
explicit target files, tests, docs, and a commit message. The prompt is a
contract, not a suggestion.

**Why safety gates must block prompt readiness.** It is not enough to *list* safety
constraints in a document; an unsafe spec must be unable to reach the
"ready_for_external_coding_agent" state at all. Every constitutional gate is
critical, and a single failure blocks readiness explicitly -- never downgraded to
a warning that a hurried operator might skim past. A spec that requests source
self-rewrite, branch creation, actuation, or an unbounded loop is blocked at
compile time, with the failing gate named.

**Why rollback and validation plans matter.** Shipping a change without a way to
undo it, or without a staged way to confirm it, is how a research codebase
accumulates silent breakage. Each pack carries a rollback plan (triggers + manual,
evidence-preserving steps -- failed artifacts are kept, never deleted) and a staged
validation plan (static inspection -> tests -> safety -> examples -> mini soak ->
ablation -> falsification replay -> replication registration, where a safety
failure blocks continuation). Neither plan executes automatically; both exist so
that an operator can implement, verify, and -- if needed -- reverse a change with
the evidence trail intact. None of this proves consciousness, life, agency, or
understanding; it is ordinary, conservative research hygiene applied to the step
where evidence becomes code.

## Phase 58 — Implementation intake, PR diff audit, and the safety regression gate

**Why implementation must be audited against evidence.** A compiler can produce a
perfect prompt pack and an external agent can return a confident summary, but the
gap between "the agent says it did X" and "the change set actually does X, safely"
is exactly where regressions enter. The intake layer closes that gap by auditing
the *artifacts* -- the diff, the test results, the generated docs -- against the
compiled spec, rather than trusting a narrative. The summary is a claim; the
evidence is the diff.

**Why tests are not enough.** A green test suite proves the tests that exist
passed; it says nothing about the tests that should exist and don't, the files
that changed outside scope, or the `import socket` quietly added in an unrelated
module. Test output is evidence, not proof of correctness. So the intake audit
treats missing safety/ClaimGuard tests as blockers, scans the diff independently
of the test result, and refuses to let a passing suite vouch for an unaudited
change.

**Why safety regressions block merge.** Most quality issues are negotiable -- a
missing doc, a coverage gap, an unknown requirement -- and resolve to
"recommend revisions". Safety regressions are not negotiable. A change that adds
source self-rewrite, automatic branching/PRs, external-agent execution,
actuation, hardware/feeder/network/shell access, or an unsupported consciousness
claim is a critical finding that blocks the merge recommendation outright, and is
reported prominently rather than averaged away. Crucially, a safety regression is
never hidden behind passing tests: the regression scan is independent of the test
audit.

**Why advisory reports preserve human authority.** The single most important
property of this layer is what it cannot do. It does not merge, approve, open, or
create pull requests; it does not call GitHub, run Git, edit source, or run an
external agent. It writes a recommendation -- recommend / revisions / block -- and
a human operator decides. This is deliberate: the moment a system can both judge
an implementation and merge it, the human is out of the loop on the one decision
that must stay human. The recommendation is advisory by construction, and the
runtime simply lacks the capability to act on it.

**How failed implementations become architecture evidence.** A blocked
implementation is not a dead end; it is data. The intake layer emits its merge
recommendation, spec-compliance status, blocked reason, safety-regression
findings, and missing-evidence list as structured outputs that the Architecture
Evolution Lab can later use to revise the experiment queue -- e.g. to require more
evidence, narrow a spec, or retire a brittle approach. Failed, missing, and
falsified evidence is preserved, never deleted, so the next compile-implement-audit
loop starts from an honest record rather than a flattering one. None of this
proves consciousness, life, agency, or understanding; it is ordinary,
conservative review hygiene applied to the step where an external implementation
re-enters the codebase.

## Phase 59 — Post-merge evidence assimilation, baseline registry, regression watch

**Why merge is not the end of evidence.** It is tempting to treat a merged PR as a
finished result -- the change passed review, it is in the tree, done. But a merge
is a decision, not a measurement. The interesting question begins *after* the
merge: what did this change actually do to the experimental architecture's
behavior? Post-merge assimilation exists because the research record must continue
past the merge boundary, ingesting the validation evidence a human gathered and
turning a code event into a measured baseline.

**Why a new baseline must be watched.** Each accepted change creates a new
baseline, and a baseline that is never compared to its parent is just a hope. The
registry is append-only and every candidate is compared dimension-by-dimension to
the baseline it descends from, so a regression introduced by an otherwise-welcome
change cannot hide. Watching the new baseline -- rather than assuming it inherited
the parent's good properties -- is how silent drift is caught early instead of
discovered three baselines later.

**Why safety regression dominates improvements.** A change can improve a dozen
metrics and break one safety boundary, and the naive aggregate would call it a net
win. That arithmetic is exactly wrong for this system. The comparison and
regression watch are built so that a safety regression dominates every positive
metric: a single critical regression blocks baseline validation regardless of how
much else improved. Safety is not a term in a weighted sum; it is a gate.

**Why follow-up soak/replication matters after merge.** A validated baseline is a
hypothesis, not a conclusion. The follow-up queue therefore recommends a mini
soak, a falsification replay, and a replication-registry entry for every validated
baseline, so the post-merge state re-enters the same conservative evidence loop the
rest of the program uses. A merge that is never soaked or replicated is an
unconfirmed claim; the queue makes the confirmation work explicit (without
executing it).

**Why post-merge assimilation preserves human authority.** The single most
important property is what this layer cannot do. A human merged the change; Solaris
only reads the local evidence that human provided. It runs no Git, calls no GitHub,
creates/approves/merges no pull request, modifies no source, and executes no
validation command -- it writes advisory reports and an append-only ledger. The
recommendations (validate, regression-watch, rollback) are metadata for a human to
act on, and a critical safety failure or missing critical evidence blocks
validation outright. The merge decision, the rollback decision, and the validation
runs all remain human acts; the ledger only makes their consequences measurable.
None of this proves consciousness, life, agency, or understanding.

## Phase 60 — Versioned research baseline, reproducibility bundle, roadmap reset

**Why baselines need versioning.** A research program that cannot name the exact
state it is standing on cannot reason about what changed. After a merge is
assimilated, "the current code" is ambiguous -- which evidence, which validation,
which limitations? Versioning a validated baseline turns that ambiguity into a
named, recorded reference point. Crucially, this versioning is *local metadata*,
not a Git tag or release: the point is a research bookmark, not a shipped product.

**Why reproducibility matters before new experiments.** The next experimental
cycle compares against this baseline, so the baseline must be reproducible or the
comparison is meaningless. The reproducibility bundle indexes exactly what a human
needs -- Python/dependency requirements, fixtures, state directories, and the
commands to run -- and distinguishes fixture, replay, live-read-only, and
operator-provided evidence. It runs nothing itself; it is the documentation that
lets a human stand the baseline back up deliberately.

**Why limitations are part of the baseline.** A baseline that lists only its
capabilities invites false confidence. The most honest thing a snapshot can carry
is its weaknesses: missing replication, untested live data, fixture-overfit risk,
unresolved regressions. The limitation registry makes these first-class and
operator-visible, and a critical limitation blocks validated status outright. A
baseline's limitations are as much a part of its identity as its capabilities.

**Why safety boundaries define the experimental envelope.** Every baseline report
restates the constitutional envelope -- no actuation, no hardware/feeder/network,
no source self-rewrite, no Git/GitHub automation, no unsupported claims -- because
the envelope is what makes the whole program safe to iterate on. The boundaries
are held by design (the runtime has no capability to cross them), and a supplied
safety artifact that *fails* downgrades the corresponding boundary and blocks
validation. The envelope is not assumed; it is stated and checked in every
snapshot.

**Why a research baseline is not a product release.** This is the phrase repeated
in every report for a reason: a validated baseline means the implementation and
evidence boundaries are documented and reproducible enough for the next cycle --
nothing more. It is not a GitHub release, not a deployment, not a certification of
intelligence, and not a claim about consciousness, life, or agency. The runtime
creates no tag, no release, no branch, and no PR; the word "validated" is a
research-hygiene status, not a marketing claim.

**How baseline resets prevent architecture drift.** Without a reset, each cycle
quietly inherits the previous cycle's assumptions, and the architecture drifts on
unexamined ground. The next-cycle roadmap reset establishes the clean starting
point explicitly -- the version, capability map, limitations, comparison anchors,
and the prioritized next experiments -- and hands it to the Architecture Evolution
Lab. Each cycle therefore begins from a named, reproducible, limitation-annotated
baseline rather than from accumulated, unstated drift. None of this proves
anything about consciousness or understanding; it is ordinary, conservative
research bookkeeping applied to the boundary between cycles.

## Notes on the Closed Research Cycle Orchestrator

**Why a closed-cycle tracker, and why it tracks rather than acts.** The project
has accumulated many stages -- baseline, roadmap, architecture evolution,
experiment compilation, implementation intake, post-merge assimilation, soak,
replication, falsification -- each with its own artifacts and its own report. What
was missing was a single, honest answer to *where are we, what supports it, what
is blocked, and what should the operator do next?* The research cycle orchestrator
provides that answer and nothing more. It is deliberately a tracker, not a driver:
the moment a meta-layer can advance the program it is no longer reporting the
program's state, it is choosing it -- and the choice of what to run, merge, or
believe must stay with the human operator. So the orchestrator reads local
artifacts and writes reports; it executes nothing.

**Why the state is derived from evidence, not asserted.** A stage the system can
*declare* it has reached is a stage it can lie about. Instead the cycle stage is
derived from which evidence is actually present: the furthest stage with
supporting artifacts wins, and every missing artifact stays visible in the state.
A cycle cannot claim "research baseline validated" without a validated baseline
report, and it cannot claim "merged" without post-merge evidence. The state is a
read of the evidence, not a self-assessment, which is exactly why it can never
approve itself.

**Why the evidence ledger is append-only and preserves failure.** The strongest
temptation in any research program is to quietly drop the experiments that did not
work. The evidence continuity ledger makes that impossible: negative, falsified,
and missing evidence are first-class, preserved entries, and superseding a stale
result marks it superseded rather than deleting it. A falsified claim from cycle 3
is still visible in cycle 7. This is what lets the artifact graph keep
contradictions visible instead of collapsing conflicting results into a single
score -- the conflict *is* the finding.

**Why operator decisions can never be auto-approved.** The promotion gates
(merge, research baseline, next cycle) require an explicit local operator decision
artifact; until one exists, the gate reports `waiting_for_operator`, never
`pass`. The system cannot invent operator approval, an operator approval cannot
override a critical safety failure or erase missing evidence, and an operator
rejection is preserved. This is the structural reason the orchestrator cannot
bootstrap itself forward: the one thing it most needs to advance -- approval -- is
the one thing it is forbidden to produce. A critical safety blocker, likewise, can
never be bypassed by any decision. None of this implies the orchestrator
understands the program it tracks, decides anything, or is in any sense an agent;
it is conservative research bookkeeping about the state of, and the gates between,
experimental cycles.

## Notes on the Scientific Claim Registry

**Why claim discipline matters.** A research program accumulates evidence faster
than it accumulates warranted claims, and the gap between the two is exactly where
hype lives. Every prior layer produces artifacts -- traces, metrics, soak dossiers,
replication matrices -- and it is tempting to read each suggestive number as a
finding. The scientific claim registry exists to break that reflex: evidence does
not automatically become a claim. A claim is registered only with its evidence
mapping, its counterevidence, its strength, and its limitations attached, and a
claim with no evidence basis is recorded as *unsupported* rather than quietly
dropped or quietly promoted. The point is not to suppress ambition; it is to keep
ambition and evidence in separate columns so the difference stays legible.

**How to distinguish the claim grades.** *Supported* means mapped evidence backs
the claim and it survived replication or strong controls; *weakly supported* means
a single direct observation with no replication; *partially supported* means
moderate evidence (two or more supporting factors) without replication;
*inconclusive* means the evidence neither supports nor refutes; *unsupported* means
no supporting evidence exists; *contradicted* means evidence points against it
without a formal falsification; *falsified* means a falsification test refuted a
core claim; and *forbidden* means the claim asserts an inner state we will not
assert at all. These grades are not a ranking of importance -- an inconclusive
result can be more scientifically interesting than a supported one -- they are a
ranking of *what the evidence licenses us to say*.

**Why limitations are first-class.** A limitation buried in a final paragraph is a
limitation designed to be skipped. Here limitations are mandatory, specific, and
linked to the claims they constrain, and they appear in the claim tables, not only
at the end. The mandatory limitations -- no consciousness, subjective, agency, or
real-world-actuation evidence -- are always present regardless of what was found,
because their absence from a report would itself be a misleading signal.

**Why counterevidence is not an embarrassment.** Failed replications, passive-parser
equivalence, fixture overfit, and missing live data are not blemishes to be
minimised; they are findings. The registry keeps counterevidence as visible as
evidence and lets it downgrade or block a claim, because a claim that cannot survive
its own counterevidence was never a claim, only a hope. Treating counterevidence as
inconvenient is the precise failure mode that claim discipline is built to prevent.

**Why consciousness/life/agency claims remain forbidden.** No measurement in this
system bears on consciousness, sentience, biological life, personhood, agency, free
will, emotion, feeling, understanding, self-awareness, or subjective experience, so
no evidence could support such a claim and none is permitted as an assertion. These
terms may appear only as explicit disclaimers; ambiguous wording ("seems aware",
"as if it feels") is flagged; and any dossier that asserts a forbidden claim is
blocked outright. This is not modesty about results -- it is accuracy about what the
results are *about*.

**How publication readiness differs from research interest.** A result can be deeply
interesting and not remotely publishable, and the dossier keeps the two apart.
Publication readiness asks a narrow question: does a draft evidence compilation
assert only supported claims, include its negative and inconclusive results and
safety boundaries, hide no limitation, and pass ClaimGuard with safety evidence
intact? A forbidden assertion, a failed safety boundary, or blocking counterevidence
makes a dossier *not ready* no matter how interesting the underlying work is. The
dossier is a draft evidence compilation, never a release, and the decision to do
anything with it remains the human operator's.

## Notes on Independent Reproducibility Review

**Why independent review matters.** A project can convince itself of almost
anything. Internal review shares the internal assumptions, the internal vocabulary,
and the internal hopes; it is structurally unable to see the gaps it was built
around. Independent review -- a stranger, ideally a hostile one, with the artifacts
and the commands -- is the only check that does not inherit those blind spots. The
independent review layer does not perform that review (no machine can review on a
human's behalf); it prepares the package so that a real external reviewer *could*,
locally and offline, without anything being published or uploaded.

**Why reproducibility challenges are stronger than summaries.** A summary asks the
reader to trust the author's reading of the evidence; a reproducibility challenge
asks the reader to run the demo and read the evidence themselves. The difference is
the difference between "we observed X" and "here is the command; run it and see
whether you observe X". So the reviewer pack leads with challenges -- fixture
demos, falsification replays, passive-parser and ablation controls, shuffled-order
and random-label tests -- each with the expected artifact and an explicit reading
of what a failure means. A challenge whose prerequisite artifact is missing is
marked *unavailable*, never quietly skipped, because an un-runnable check is itself
information about the state of the evidence.

**Why adversarial alternatives must be preserved.** For every apparent result there
is a deflationary explanation: it was log accumulation, fixture overfit, label
leakage, a lucky seed, a passive parser. The temptation is to rebut these once and
move on. The adversarial engine instead keeps every alternative on the record, each
with the specific evidence that would reduce its uncertainty, and lets a strong
unaddressed alternative downgrade review readiness. An alternative explanation is
not an insult to the work; it is a map of what the work has not yet ruled out.

**Why external review readiness is not claim strength.** A weak or even negative
result can be perfectly ready for hostile external review -- if its artifacts are
present, its claims map to evidence, its counterevidence is visible, its
limitations are specific, and its commands reproduce. Conversely, a strong-sounding
result with missing artifacts, a critical sanitizer leak, or an asserted forbidden
claim is *not* ready, however exciting it sounds. Readiness measures whether the
evidence is inspectable, not whether the conclusion is impressive. Conflating the
two is exactly how hype enters a review pipeline.

**Why reviewer objections are evidence, not annoyance.** An objection records a way
the evidence might be wrong, and that is the most useful thing a reviewer produces.
The response ledger is append-only: objections cannot be deleted, an objection
accepted as a limitation or a falsification stays permanently visible, and a
response must cite evidence or admit it has none. The system is structurally
forbidden from declaring victory over a reviewer by default -- an unanswered
objection stays open. Treating objections as a queue to be cleared, rather than as
findings to be preserved, would defeat the entire purpose of preparing for review.
