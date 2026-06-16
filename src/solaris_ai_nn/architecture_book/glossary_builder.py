"""Glossary builder -- technical definitions, claim-constrained.

:class:`GlossaryBuilder` defines the project's terms technically, avoids mystical
language, and adds "not consciousness/life/personhood" clarifications where the
term could be misread. "Organismic" and related terms are defined as architectural
metaphors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


# (term, definition). Definitions are technical and claim-constrained.
_GLOSSARY: Tuple[Tuple[str, str], ...] = (
    ("Solaris-AI-NN",
     "A local research architecture of bounded recurrent/reservoir substrates and "
     "scientific-governance layers. It is a research codebase, not a product and "
     "not a claim of intelligence."),
    ("Solaris_Ai",
     "The reference project this codebase derives from; a continuous, "
     "event-driven substrate. Solaris-AI-NN reconstructs and extends its ideas in "
     "Python."),
    ("organismic substrate",
     "Architectural metaphor for the layered sensorium->cognition->action stack. "
     "It denotes a software organization, NOT biological life."),
    ("plural sensorium",
     "Multiple heterogeneous sensory channels (human-like and non-human-like) "
     "feeding the substrate; not a sensory experience claim."),
    ("sensory membrane",
     "The read-only boundary that converts inputs into bounded internal signals; "
     "sensory text is never treated as an operator command."),
    ("field",
     "A bounded stream of synthetic or read-only environmental signals the "
     "sensorium consumes."),
    ("feeder",
     "An external, operator-run source of read-only signals. Solaris never starts "
     "or controls feeders."),
    ("read-only feeder",
     "A feeder whose data is only read; no actuation or write-back occurs."),
    ("sensorium differentiation",
     "Study of whether different sensory configurations produce measurably "
     "different internal structure."),
    ("perceptual metabolism",
     "Bounded regulation of representational load (intake, consolidation, decay); "
     "a homeostatic mechanism, not digestion or life."),
    ("ontogenesis",
     "Sensorium-native formation of internal structure over time; an "
     "architectural process, not biological development."),
    ("proto-concept",
     "A recurring internal feature cluster; a measured regularity, not a human "
     "concept or understanding."),
    ("semiogenesis",
     "Formation of internal private signs that index regularities; not language "
     "and not meaning in the human sense."),
    ("private sign",
     "An internal label with no external semantics asserted; useful only if it "
     "has downstream effect."),
    ("sensorium-native cognition",
     "Bounded internal transformations over sensorium-derived state; "
     "'cognition-like', not understanding or thought."),
    ("self-boundary",
     "An operational distinction between internal state and input; not "
     "self-awareness or a self."),
    ("continuity trace",
     "A record that internal state persisted across time/restarts; a bookkeeping "
     "trace, not memory in the human sense."),
    ("valence",
     "A scalar internal pressure signal (e.g. toward/away); not emotion or "
     "feeling."),
    ("desire",
     "Operational pressure that biases internal action selection; not a wish, "
     "want, or subjective desire."),
    ("internal action",
     "A bounded internal state change; not a real-world action and not actuation."),
    ("action-reaction",
     "Learning that internal actions have internal consequences; not agency or "
     "free will."),
    ("consequence trace",
     "A recorded internal effect of an internal action."),
    ("habit",
     "A stabilized internal action pattern; a statistical regularity, not a "
     "choice."),
    ("inhibition",
     "Bounded suppression of an internal action; a control mechanism, not will."),
    ("developmental life",
     "Long-horizon bounded runtime tracking internal change. 'Life' is metaphor; "
     "no biological life is claimed."),
    ("soak",
     "A long, bounded run that checks stability and growth-vs-accumulation over "
     "time."),
    ("replication",
     "Re-running an experiment across seeds/runs to test whether a result holds."),
    ("falsification",
     "Tests designed to refute a claim; surviving falsification strengthens, "
     "failing it weakens or blocks a claim."),
    ("architecture evolution",
     "A lab that proposes architecture variants from evidence; it proposes only "
     "and modifies no source."),
    ("experiment compiler",
     "Turns proposals/gaps into implementation/experiment specification packs for "
     "external humans/agents; executes nothing."),
    ("implementation intake",
     "Audits externally implemented changes (diff/test/safety/ClaimGuard) before a "
     "human merge; merges nothing itself."),
    ("research baseline",
     "A versioned local reproducible reference point; not a release and not a "
     "consciousness claim."),
    ("research cycle",
     "The closed orchestrator tracking where the program is across experimental "
     "cycles; it executes nothing."),
    ("scientific claim registry",
     "An append-only registry mapping evidence to claims and blocking unsupported "
     "or forbidden claims."),
    ("theory ledger",
     "Working hypotheses under evidence, with revisions preserved; theory is not "
     "proof."),
    ("independent review",
     "A local, offline reviewer pack and reproducibility challenge set; it "
     "publishes nothing and contacts no one."),
    ("review assimilation",
     "Turning reviewer objections and reproduction outcomes into claim revisions "
     "and experiment recommendations; not model training."),
    ("ClaimGuard",
     "A scanner that flags unsupported inner-state claims in generated text; "
     "failure blocks publication readiness."),
    ("Inner MAP",
     "The substrate's read-only self-model/observer; a status view, not "
     "self-awareness."),
    ("operator console",
     "The local query interface for inspecting system state; sensory text is "
     "never an operator command."),
    ("Alpha Research System",
     "The unified local CLI assembling the modules into one bounded, fixture-only "
     "research run; not a product release."),
)


@dataclass
class GlossaryEntry:
    """One glossary term + technical definition."""

    term: str
    definition: str

    def to_dict(self) -> Dict[str, Any]:
        return {"term": self.term, "definition": self.definition}

    def render_md(self) -> str:
        return f"- **{self.term}** -- {self.definition}"


@dataclass
class GlossaryBuilder:
    """Builds the technical glossary."""

    def build(self) -> List[GlossaryEntry]:
        return [GlossaryEntry(term=t, definition=d) for t, d in _GLOSSARY]

    def summary(self) -> Dict[str, Any]:
        entries = self.build()
        return {
            "glossary_entry_count": len(entries),
            "entries": [e.to_dict() for e in entries],
            "note": "terms are defined technically; 'organismic' and related "
                    "terms are architectural metaphors and carry explicit "
                    "not-consciousness/life/personhood clarifications",
        }

    def render_md(self) -> str:
        lines = ["# Solaris-AI-NN Glossary", "",
                 "_Technical definitions. 'Organismic', 'life', 'desire', "
                 "'cognition', and similar terms are architectural metaphors and "
                 "denote software mechanisms only. The system makes no claim of "
                 "consciousness, sentience, biological life, personhood, agency, "
                 "free will, emotion, feeling, understanding, self-awareness, or "
                 "subjective experience._", ""]
        for e in self.build():
            lines.append(e.render_md())
        return "\n".join(lines) + "\n"
