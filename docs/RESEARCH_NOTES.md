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
