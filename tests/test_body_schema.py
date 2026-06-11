"""Tests for the simulated body schema."""

from __future__ import annotations

from solaris_ai_nn.ego.body_schema import (
    ActionAuthority,
    BodySchema,
    EmbodimentPerspective,
)


def test_simulated_body_schema_generated():
    schema = BodySchema.from_embodiment({
        "position": (3, 4), "energy": 7.5, "max_energy": 10.0})
    assert schema.body_exists is True
    assert schema.body_type == "simulated_grid_body"
    assert schema.position == (3, 4)
    assert schema.energy == 7.5
    assert schema.environment_scope == "grid_world"
    assert schema.available_actions  # the declared ACTION_SPACE
    assert "rest" in schema.available_actions


def test_action_authority_simulation_only():
    schema = BodySchema.from_embodiment({"energy": 5.0})
    assert schema.action_authority == ActionAuthority.SIMULATION_ONLY
    none = BodySchema.from_embodiment(None)
    assert none.body_exists is False
    assert none.action_authority == ActionAuthority.NONE
    assert ActionAuthority.FORBIDDEN_EXTERNAL in ActionAuthority.ALL


def test_physical_embodiment_not_claimed():
    schema = BodySchema.from_embodiment({"energy": 5.0})
    data = schema.to_dict()
    assert "no physical embodiment" in data["note"]
    assert "no physical embodiment" in data["boundary"]["note"]
    assert "any real-world actuation" in schema.forbidden_actions
    # The boundary names physical hardware as outside.
    assert "physical hardware" in schema.boundary.outside


def test_perspective_is_simulated():
    schema = BodySchema.from_embodiment({"energy": 5.0})
    perspective = schema.perspective()
    assert isinstance(perspective, EmbodimentPerspective)
    assert perspective.evidence_status == "simulated"
    assert perspective.environment_scope == "grid_world"
    assert "simulated movement" in perspective.acting_through
