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
