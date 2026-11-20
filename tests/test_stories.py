"""
Tests for named stories (Story) and base_elevation on StructuralModel.
"""

import math
import pytest

from struct_core import (
    Node,
    Project,
    Story,
    StructuralModel,
    StructuralValidationError,
    Support,
    validate_structural_model,
)


def test_story_validation_and_lookup():
    s1 = Story(name="Story1", elevation=3.5)
    s2 = Story(name="Roof", elevation=7.0)
    model = StructuralModel(
        units="kN, m",
        base_elevation=0.0,
        stories=[s1, s2],
        nodes=[Node(id="1", x=0.0, y=0.0, z=0.0)],
        supports=[Support.fixed_3d("1")],
    )
    assert model.base_elevation == 0.0
    assert model.get_story("Story1") == s1
    assert model.get_story("Roof") == s2
    assert model.get_story("Missing") is None
    assert not hasattr(model, "story_elevations")
    validate_structural_model(model)

    # Blank story name refused
    with pytest.raises(ValueError, match="empty or whitespace"):
        Story(name="   ", elevation=3.5)

    # Non-finite elevation refused
    with pytest.raises(ValueError, match="finite"):
        Story(name="Bad", elevation=math.nan)


def test_base_elevation_has_no_default_of_zero():
    model = StructuralModel()
    assert model.base_elevation is None
    assert model.stories == []


def test_validate_stories_errors():
    base_nodes = [Node(id="1", x=0.0, y=0.0, z=0.0)]
    base_supports = [Support.fixed_3d("1")]

    # Duplicate story name
    m_dup_name = StructuralModel(
        nodes=base_nodes,
        supports=base_supports,
        base_elevation=0.0,
        stories=[Story(name="S1", elevation=3.5), Story(name="S1", elevation=7.0)],
    )
    with pytest.raises(StructuralValidationError, match="Duplicate Story name"):
        validate_structural_model(m_dup_name)

    # Duplicate story elevation
    m_dup_elev = StructuralModel(
        nodes=base_nodes,
        supports=base_supports,
        base_elevation=0.0,
        stories=[Story(name="S1", elevation=3.5), Story(name="S2", elevation=3.5)],
    )
    with pytest.raises(StructuralValidationError, match="Duplicate Story elevation"):
        validate_structural_model(m_dup_elev)

    # Story at or below base_elevation
    m_below = StructuralModel(
        nodes=base_nodes,
        supports=base_supports,
        base_elevation=1.0,
        stories=[Story(name="S1", elevation=1.0)],
    )
    with pytest.raises(StructuralValidationError, match="strictly above base_elevation"):
        validate_structural_model(m_below)


def test_project_delegates_and_converts_base_elevation_and_stories():
    proj = Project(units="kN, m")
    proj.base_elevation = -2.0
    proj.stories = [Story(name="Ground", elevation=0.0), Story(name="Roof", elevation=4.0)]
    assert proj.model.base_elevation == -2.0
    assert [(s.name, s.elevation) for s in proj.model.stories] == [("Ground", 0.0), ("Roof", 4.0)]

    proj.convert_units("kip, ft")
    assert proj.model.base_elevation == pytest.approx(-2.0 * 3.28084, rel=1e-4)
    assert proj.model.stories[0].name == "Ground"
    assert proj.model.stories[0].elevation == pytest.approx(0.0, abs=1e-9)
    assert proj.model.stories[1].name == "Roof"
    assert proj.model.stories[1].elevation == pytest.approx(4.0 * 3.28084, rel=1e-4)
