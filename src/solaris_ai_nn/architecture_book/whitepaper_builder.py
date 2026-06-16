"""Whitepaper builder -- the full technical whitepaper (Markdown).

:class:`TechnicalWhitepaperBuilder` generates the technical whitepaper and the
shorter technical overview. Both state explicitly that Solaris-AI-NN is a research
architecture (not a product claim), that "organismic" is an architectural metaphor,
that the system proves nothing about consciousness/sentience/biological-life/
personhood/agency/free-will/subjective-experience, that it is local-only by
default, and that the alpha profile is fixture-only by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_NON_CLAIMS = (
    "Solaris-AI-NN is a research architecture, not a product claim.",
    "\"Organismic\" is an architectural metaphor, not a biological assertion.",
    "The system does not prove consciousness.",
    "The system does not prove sentience.",
    "The system does not prove biological life.",
    "The system does not prove personhood.",
    "The system does not prove agency or free will.",
    "The system does not prove subjective experience.",
    "The system is local-only by default.",
    "The alpha profile is fixture-only by default.",
)


@dataclass
class TechnicalWhitepaperBuilder:
    """Builds the technical whitepaper and technical overview Markdown."""

    module_summary: Dict[str, Any] = field(default_factory=dict)

    # -- whitepaper ---------------------------------------------------------

    def build_whitepaper(self) -> str:
        s: List[str] = []
        s.append("# Solaris-AI-NN: Technical Whitepaper")
        s.append("")
        s.append("## 1. Abstract")
        s.append(
            "Solaris-AI-NN is a local research architecture that organizes a "
            "bounded recurrent/reservoir substrate into a layered, "
            "scientifically-governed stack: a plural sensorium feeds perceptual "
            "metabolism, ontogenesis, semiogenesis, cognition-like "
            "transformations, an operational self-boundary, valence/desire "
            "pressure, and action-reaction learning, observed over long-horizon "
            "bounded runtimes. A scientific testing layer (soak, replication, "
            "falsification, controls) produces evidence; a governance layer "
            "(architecture evolution, experiment compiler, implementation "
            "intake, post-merge assimilation, research baseline, research cycle) "
            "tracks the program; and a claim/review layer (scientific claim "
            "registry, theory ledger, independent review, reviewer feedback "
            "assimilation) constrains what may be said. A unified local CLI (the "
            "Alpha Research System) runs the whole chain in a bounded, "
            "fixture-only mode. This whitepaper documents the architecture and "
            "the evidence/claim discipline; it asserts nothing about minds.")
        s.append("")
        s.append("## 2. Scope and Non-Claims")
        s.append("This document is a technical/scientific explanation, not "
                 "marketing and not a public release. Explicitly:")
        s.append("")
        s += [f"- {c}" for c in _NON_CLAIMS]
        s.append("")
        s.append("## 3. Research Motivation")
        s.append(
            "The motivating question is narrow and falsifiable: does organizing "
            "a bounded substrate around a plural sensorium and an internal "
            "metabolism/development loop produce measurable internal structure "
            "that a passive parser, a fixture overfit, or log accumulation does "
            "not? The architecture exists to make that question testable, and to "
            "make the answer auditable, rather than to assert any conclusion.")
        s.append("")
        s.append("## 4. Background: From Continuous Solaris_Ai to Solaris-AI-NN")
        s.append(
            "Solaris_Ai is a continuous, event-driven substrate. Solaris-AI-NN "
            "reconstructs its ideas in a bounded, local, reproducible Python "
            "codebase and adds the scientific-governance machinery needed to "
            "test claims about it. The 'NN' substrate is reservoir/recurrent, "
            "chosen for long-runtime, low-compute, event-driven operation rather "
            "than large-scale deep learning.")
        s.append("")
        s.append("## 5. Design Principles")
        s += ["- Local-only and bounded by default: no network, shell, Git, or "
              "actuation from the runtime.",
              "- Evidence before claims: nothing becomes a claim without mapped "
              "evidence, and counterevidence is preserved.",
              "- Honest gaps: missing modules, missing evidence, and limitations "
              "are always shown, never hidden.",
              "- Metaphor discipline: 'organismic', 'life', 'desire', and "
              "'cognition' name mechanisms, not minds.",
              "- Operator authority: the human operator decides; the system "
              "proposes and reports."]
        s.append("")
        s.append("## 6. System Architecture")
        s.append(
            "The architecture is a pipeline of bounded modules from sensorium to "
            "action, wrapped by testing, governance, and claim/review layers, "
            "and assembled by the Alpha Research System. See the architecture "
            "book for the full module-by-module treatment and the Mermaid system "
            "map.")
        s.append("")
        s.append("## 7. Organismic Core Loop")
        s.append(
            "Stimulus -> internal push -> desire/valence pressure -> internal "
            "action -> reaction -> consequence -> memory/continuity -> habit -> "
            "future perception. The loop is entirely internal and bounded; no "
            "step actuates anything in the world.")
        s.append("")
        s.append("## 8. Sensorium and Perception")
        s.append(
            "The plural sensorium converts heterogeneous (human-like and "
            "non-human-like) read-only inputs into bounded internal signals "
            "through a read-only sensory membrane. Sensory text is never treated "
            "as an operator command, and feeders are operator-run and never "
            "started or controlled by the system.")
        s.append("")
        s.append("## 9. Internal Developmental Processes")
        s.append(
            "Perceptual metabolism regulates representational load; ontogenesis "
            "forms internal structure; semiogenesis forms private signs; "
            "cognition-like transformations operate over sensorium-derived "
            "state; a self-boundary distinguishes internal state from input; "
            "valence/desire bias internal action; action-reaction learns "
            "internal consequences. None of these assert understanding, feeling, "
            "or agency.")
        s.append("")
        s.append("## 10. Evidence and Testing Methodology")
        s.append(
            "Long-horizon soak runs check stability and distinguish development "
            "from log accumulation; cross-run replication tests whether results "
            "hold across seeds; the falsification lab tries to refute claims; "
            "controls and ablations (passive parser, no-metabolism, "
            "no-semiogenesis, shuffled order, random labels) provide the "
            "counterfactuals. Evidence is recorded as artifacts, including "
            "negative and inconclusive results.")
        s.append("")
        s.append("## 11. Safety and Governance")
        s.append(
            "Every layer carries a safety validator enforcing local-only, "
            "bounded, non-actuating, non-publishing, non-Git/GitHub operation. "
            "Architecture evolution, experiment compiler, implementation intake, "
            "post-merge assimilation, research baseline, and research cycle "
            "govern how the program changes -- always proposal-first, with the "
            "human merging code outside the system.")
        s.append("")
        s.append("## 12. Alpha Research System")
        s.append(
            "The Alpha Research System is the unified local CLI that assembles "
            "the modules into one bounded, fixture-only end-to-end run "
            "(state -> doctor -> module registry -> demo -> claims -> review -> "
            "cycle status -> alpha report). It is reached via "
            "`python -m solaris_ai_nn`. It is not a product release.")
        s.append("")
        s.append("## 13. Scientific Claim Discipline")
        s.append(
            "The scientific claim registry maps evidence to claims, grades their "
            "strength, preserves counterevidence and falsified results, and "
            "blocks forbidden inner-state claims. The theory ledger keeps "
            "hypotheses under evidence. Publication readiness is advisory and "
            "blocked by forbidden claims, failed reproductions, or unresolved "
            "critical objections.")
        s.append("")
        s.append("## 14. Independent Review and Reproducibility")
        s.append(
            "The independent review layer prepares a local, offline reviewer "
            "pack, reproducibility challenges, an audit matrix, and an "
            "append-only response ledger; it publishes nothing and contacts no "
            "one. Reviewer feedback assimilation turns objections and "
            "reproduction outcomes into claim revisions and experiment "
            "recommendations -- as research evidence, never as model training.")
        s.append("")
        s.append("## 15. Limitations")
        s += ["- Results to date are bounded and largely fixture-based; live "
              "evidence is limited and governance-gated.",
              "- Optional modules may be absent; the system reports them as "
              "missing rather than substituting their output.",
              "- No claim about consciousness, life, agency, or subjective "
              "experience is supported, made, or measurable.",
              "- The architecture is a research scaffold; it is not validated as "
              "a product and creates no release."]
        s.append("")
        s.append("## 16. Future Work")
        s.append(
            "Governed live read-only runs, longer soaks, stronger controls and "
            "replication, deeper falsification of the central claims, and "
            "external reproduction using the local reviewer pack. Each step is "
            "gated by evidence and operator decision.")
        s.append("")
        s.append("## 17. Appendix: Module Index")
        s.append("See `SOLARIS_AI_NN_MODULE_MAP.md` and "
                 "`SOLARIS_AI_NN_APPENDICES.md` for the full prompt-to-module "
                 "mapping, artifact directories, CLI reference, and the forbidden "
                 "claim index.")
        s.append("")
        s.append("---")
        s.append("_This whitepaper is local Markdown documentation. It was not "
                 "published or uploaded, no Git/GitHub operation occurred, no "
                 "experiments were executed to produce it, and it makes no claim "
                 "of consciousness, sentience, biological life, personhood, "
                 "agency, free will, emotion, feeling, understanding, "
                 "self-awareness, or subjective experience._")
        return "\n".join(s) + "\n"

    # -- technical overview -------------------------------------------------

    def build_overview(self) -> str:
        s: List[str] = []
        s.append("# Solaris-AI-NN: Technical Overview")
        s.append("")
        s.append("## One-paragraph summary")
        s.append(
            "Solaris-AI-NN is a local, bounded research architecture that wraps a "
            "recurrent/reservoir substrate in a layered sensorium-to-action stack "
            "and a full scientific-governance pipeline (long-horizon testing, "
            "architecture governance, claim governance, and independent review), "
            "assembled behind a single local command-line interface. It is a "
            "scaffold for testing narrow, falsifiable questions about whether "
            "organizing a bounded substrate in a particular way produces "
            "measurable internal structure that simpler baselines do not. It is "
            "not a product, not a deployment, and not a claim about minds. Every "
            "layer is local-only and bounded by default, every claim is "
            "constrained by mapped evidence, and every forbidden inner-state "
            "claim (consciousness, sentience, life, personhood, agency, free "
            "will, emotion, feeling, understanding, self-awareness, subjective "
            "experience) is blocked rather than asserted.")
        s.append("")
        s.append("## Architectural thesis")
        s.append(
            "The thesis Solaris-AI-NN is built to test is deliberately modest and "
            "refutable: if a bounded recurrent substrate is organized around a "
            "plural sensorium and an internal metabolism/development loop, then "
            "internal structure may emerge -- recurring feature clusters, "
            "private internal signs, stabilized internal action patterns -- that "
            "a passive parser, a fixture-overfit model, or mere log accumulation "
            "would not produce. The architecture does not assert that this is "
            "true. Its entire purpose is to make the question testable and the "
            "answer auditable: to produce the evidence, the controls, the "
            "falsification attempts, and the claim discipline needed for a "
            "technically competent reader to decide for themselves. Where the "
            "evidence is weak, the system says so; where a control has not been "
            "run, the system records the gap; and where a claim would exceed the "
            "evidence, the system blocks it. The thesis is a research hypothesis "
            "under continuous test, not a conclusion.")
        s.append("")
        s.append("## Core loop")
        s.append(
            "The organismic core loop is the heart of the substrate and is "
            "entirely internal: a stimulus arrives through the read-only sensory "
            "membrane; it produces an internal push; valence/desire pressure "
            "biases an internal action; the internal action yields a reaction and "
            "a recorded internal consequence; the consequence updates memory and "
            "the continuity trace; repeated consequences stabilize into habits; "
            "and those habits shape future perception, closing the loop. No step "
            "in this loop actuates anything in the world, drives any device, or "
            "starts any feeder. 'Action' here means a bounded internal state "
            "change, 'desire' means an operational pressure signal, and "
            "'consequence' means a recorded internal effect -- the loop is a "
            "software control cycle, and the organismic vocabulary names "
            "mechanisms, not experiences. The loop runs under a strict tick and "
            "runtime budget so that long-horizon behaviour can be studied without "
            "any unbounded computation.")
        s.append("")
        s.append("## Module stack")
        s.append(
            "The substrate is a pipeline of bounded software modules. The plural "
            "sensorium converts heterogeneous human-like and non-human-like "
            "read-only inputs into internal signals; the read-only field and "
            "feeder SDK define how external, operator-run sources are consumed "
            "without ever being started or controlled by the system. Perceptual "
            "metabolism regulates representational load (intake, consolidation, "
            "decay) so the substrate stays bounded over long runtimes. "
            "Sensorium-native ontogenesis forms internal structure over time; "
            "semiogenesis forms private internal signs that index regularities; "
            "sensorium-native cognition performs bounded transformations over "
            "sensorium-derived state; the self-boundary maintains an operational "
            "distinction between internal state and input; valence/desire supply "
            "internal pressure; and action-reaction learns the internal "
            "consequences of internal actions, observed over long-horizon "
            "development. Each module is independently runnable, exposes a "
            "bounded status view, and is listed -- with its package path and "
            "implementation status -- in the module map. Where a module is "
            "absent, the system reports it as missing rather than substituting "
            "its output.")
        s.append("")
        s.append("## Research / testing stack")
        s.append(
            "Producing internal structure is not the same as showing it is real, "
            "so a scientific testing stack sits above the substrate. The "
            "developmental soak protocol runs long, bounded sessions and checks "
            "stability and -- critically -- whether apparent growth tracks "
            "development or merely the size of an accumulating log. Evidence "
            "dossiers and a post-run autopsy record what happened, including "
            "negative and inconclusive results. Cross-run replication re-runs "
            "experiments across seeds to test whether a result holds, and the "
            "falsification lab actively tries to refute claims. Controls and "
            "ablations -- a passive-parser control, no-metabolism and "
            "no-semiogenesis ablations, shuffled temporal order, and "
            "random-label-same-features tests -- provide the counterfactuals that "
            "distinguish a genuine effect from fixture overfit, human-label "
            "leakage, a lucky seed, or passive-parser equivalence. The testing "
            "stack is what makes the central thesis falsifiable rather than "
            "merely suggestive.")
        s.append("")
        s.append("## Governance stack")
        s.append(
            "Because the architecture is meant to evolve under evidence, a "
            "governance stack controls how it changes. The architecture evolution "
            "lab proposes variants from accumulated evidence -- proposal-only, "
            "modifying no source. The experiment compiler turns proposals and "
            "evidence gaps into implementation/experiment specification packs for "
            "an external human or agent to implement; it executes nothing. "
            "Implementation intake audits any externally implemented change "
            "(diff, tests, safety invariants, ClaimGuard) before a human merges "
            "it; the system never merges code itself. Post-merge assimilation "
            "ingests the operator-supplied evidence after a human merge; the "
            "versioned research baseline pins a reproducible local reference "
            "point (not a release); and the closed research cycle orchestrator "
            "tracks where the program stands across experimental cycles. Every "
            "step is proposal-first and human-gated: the architecture proposes "
            "and reports, and a human decides and merges outside the system.")
        s.append("")
        s.append("## Claim and review governance")
        s.append(
            "Above the evidence sits a claim/review layer whose job is to prevent "
            "the gap between evidence and rhetoric from widening. The scientific "
            "claim registry maps each claim to its supporting and contradicting "
            "evidence, grades its strength, preserves counterevidence and "
            "falsified results, and blocks forbidden inner-state claims outright. "
            "The theory ledger keeps working hypotheses under evidence, with "
            "prior versions preserved. The independent review layer prepares a "
            "local, offline reviewer pack, reproducibility challenges, an audit "
            "matrix, and an append-only response ledger -- it publishes nothing "
            "and contacts no one. Reviewer feedback assimilation turns reviewer "
            "objections and reproduction outcomes into claim revisions and "
            "experiment recommendations, treating that feedback as research "
            "evidence and never as model-training signal. Publication readiness "
            "is advisory and is blocked by forbidden claims, failed "
            "reproductions, or unresolved critical objections.")
        s.append("")
        s.append("## Alpha operation")
        s.append(
            "All of the above is assembled by the Alpha Research System into one "
            "operable entry point. A unified local CLI (`python -m "
            "solaris_ai_nn`) initializes a local state directory, runs a "
            "read-only doctor (system check), inspects the module registry, runs "
            "a bounded fixture-only end-to-end demo, and writes an alpha report, "
            "an artifact index, an operator runbook, and a cycle status with an "
            "advisory next action. The default alpha profile is fixture-only: it "
            "reads a tiny synthetic fixture stream rather than any live feed, so "
            "the entire chain can be exercised offline, reproducibly, and "
            "honestly -- with missing modules and blockers shown rather than "
            "hidden -- before any governed live read-only run is considered. "
            "Live read-only profiles exist only as metadata and remain blocked "
            "until governance artifacts are present.")
        s.append("")
        s.append("## Safety boundaries")
        s += ["- No real-world actuation, hardware, or feeder control; feeders "
              "are operator-run and never started or controlled by the system.",
              "- No network, shell, browser, or OS access from the runtime.",
              "- No Git/GitHub calls; no branch/tag/release/PR creation; no "
              "publishing or uploading of any artifact.",
              "- No source self-rewrite; the human implements and merges code "
              "outside the system.",
              "- No Human Feedback / Teaching Loop and no model training from "
              "reviewer feedback; reviewer feedback is evidence only.",
              "- No forbidden scientific claims; ClaimGuard scans all generated "
              "text and a failure blocks publication readiness.",
              "- Bounded by construction: every runtime has a positive runtime "
              "and tick budget and refuses to run unbounded."]
        s.append("")
        s.append("## What can currently be evaluated")
        s.append(
            "A reader can currently evaluate whether the bounded fixture pipeline "
            "runs end to end; whether module presence, demo steps, and skipped "
            "modules are reported honestly; whether each claim maps to evidence "
            "and whether counterevidence is preserved; whether the controls, "
            "ablations, and falsification attempts are documented; whether the "
            "reproducibility challenges are runnable locally from the reviewer "
            "pack; and whether the safety boundaries hold by construction (the "
            "runtimes have no capability to cross them). These are engineering "
            "and methodology questions with checkable answers, and the alpha "
            "report and build reports surface them directly.")
        s.append("")
        s.append("## What cannot be claimed")
        s.append(
            "Nothing in this system demonstrates, measures, or supports a claim "
            "of consciousness, sentience, biological life, personhood, agency, "
            "free will, emotion, feeling, understanding, self-awareness, or "
            "subjective experience, and no such claim is made. 'Organismic', "
            "'life', 'desire', 'cognition', and similar terms are architectural "
            "metaphors for software mechanisms. The system performs no autonomous "
            "self-improvement: it proposes changes that a human implements and "
            "merges. Solaris-AI-NN is a research scaffold for asking and testing "
            "narrow, falsifiable questions -- not a validated product, not a "
            "public release, and not proof of intelligence.")
        s.append("")
        s.append("## How to read the rest of this documentation")
        s.append(
            "This overview is the shortest entry point. The technical whitepaper "
            "(`SOLARIS_AI_NN_WHITEPAPER.md`) gives the abstract, scope and "
            "non-claims, design principles, and a section-by-section treatment of "
            "the architecture, evidence methodology, governance, and limitations. "
            "The architecture book (`SOLARIS_AI_NN_ARCHITECTURE_BOOK.md`) expands "
            "every module into a chapter with its purpose, role, inputs, outputs, "
            "artifacts, safety constraints, integration points, failure modes, "
            "limitations, implementation status, and future work, alongside the "
            "Mermaid diagrams. The module map enumerates Prompts 41-66 with their "
            "package paths and implementation status; the research roadmap lays "
            "out the ten phases and their current status; the safety-boundaries "
            "document collects the hard prohibitions; the glossary defines every "
            "term technically (with metaphor and forbidden-claim clarifications); "
            "and the appendices index the prompts, artifacts, CLI commands, "
            "safety rules, and forbidden claims. A documentation index lists all "
            "of these and marks any that are missing. Throughout, missing modules "
            "and missing evidence are shown rather than hidden, and the language "
            "remains constrained to what the evidence supports.")
        s.append("")
        return "\n".join(s) + "\n"

    def non_claims(self) -> List[str]:
        return list(_NON_CLAIMS)
