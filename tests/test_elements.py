"""
Unit tests for element schemas and registry.
"""

import pytest
from pydantic import TypeAdapter
from struct_core.structural_model.elements import (
    BeamElement,
    Element,
    SpringElement,
    TrussElement,
)
from struct_core.structural_model.registry import ElementRegistry


def test_truss_element():
    elem = TrussElement(id=1, start_node="N1", end_node="N2", section_id="Sec1")
    assert elem.id == 1
    assert elem.type == "truss"
    assert elem.start_node == "N1"
    assert elem.end_node == "N2"


def test_beam_element_with_releases():
    elem = BeamElement(
        id="B1",
        start_node=1,
        end_node=2,
        section_id="Rect",
        release_j=[False, False, True],  # Moment hinge at node j (auto-expanded to 6-DOF)
    )
    assert elem.id == "B1"
    assert elem.type == "beam"
    assert elem.release_j == [False, False, False, False, False, True]
    assert elem.include_shear_deformation is False


def test_beam_element_release_validation():
    # Invalid length (neither 3 nor 6) raises
    with pytest.raises(ValueError, match="must have 3 .* or 6 .* entries"):
        BeamElement(id="B1", start_node=1, end_node=2, section_id="S", release_i=[True, False])

    # Unstable mechanism: all released
    with pytest.raises(ValueError, match="unstable mechanism"):
        BeamElement(id="B1", start_node=1, end_node=2, section_id="S", release_i=[True] * 6, release_j=[True] * 6)

    # Unstable mechanism: u1 (axial) released at both ends
    with pytest.raises(ValueError, match="u1 .* released at both ends"):
        BeamElement(id="B1", start_node=1, end_node=2, section_id="S", release_i=[True, False, False], release_j=[True, False, False])

    # Unstable mechanism: r3 at both ends and u2 released at start
    with pytest.raises(ValueError, match="r3 .* and u2"):
        BeamElement(id="B1", start_node=1, end_node=2, section_id="S", release_i=[False, True, True], release_j=[False, False, True])


def test_beam_element_shear_deformation():
    elem = BeamElement(
        id="B2",
        start_node=1,
        end_node=2,
        section_id="Rect",
        include_shear_deformation=True,
    )
    assert elem.include_shear_deformation is True


def test_beam_element_stiffness_modifier_keys():
    """Only STIFFNESS_MODIFIER_KEYS are accepted: a misspelled or legacy key (I, As) is refused, not ignored."""
    from struct_core import STIFFNESS_MODIFIER_KEYS

    mods = {k: 0.5 for k in STIFFNESS_MODIFIER_KEYS}
    assert BeamElement(id="B", start_node=1, end_node=2, section_id="R", stiffness_modifiers=mods).stiffness_modifiers == mods
    for bad in ({"I": 0.35}, {"As": 2.0}, {"i3": 0.35}):
        with pytest.raises(ValueError, match="Unknown stiffness modifiers"):
            BeamElement(id="B", start_node=1, end_node=2, section_id="R", stiffness_modifiers=bad)



def test_spring_element():
    spring = SpringElement(id="S1", start_node=1, end_node=2, kx=1000.0, ky=500.0)
    assert spring.id == "S1"
    assert spring.kx == 1000.0


def test_element_polymorphic_parsing():
    adapter = TypeAdapter(Element)

    beam_data = {
        "type": "beam",
        "id": "E1",
        "start_node": 1,
        "end_node": 2,
        "section_id": "S1",
    }
    parsed = adapter.validate_python(beam_data)
    assert isinstance(parsed, BeamElement)
    assert parsed.start_node == 1


def test_element_registry():
    @ElementRegistry.register("custom_beam")
    class CustomBeamElement(BeamElement):
        pass

    assert "custom_beam" in ElementRegistry.list_types()
    assert ElementRegistry.get("custom_beam") == CustomBeamElement


def test_beam_element_stiffness_modifiers():
    elem = BeamElement(
        id="B_MOD",
        start_node=1,
        end_node=2,
        section_id="S1",
        stiffness_modifiers={"I3": 0.35, "I2": 0.35, "A": 0.70},
    )
    assert elem.stiffness_modifiers["I3"] == 0.35
    assert elem.stiffness_modifiers["A"] == 0.70

