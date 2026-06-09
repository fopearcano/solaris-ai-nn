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
