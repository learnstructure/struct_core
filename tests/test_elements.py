"""
Unit tests for element schemas and registry.
"""

import pytest
from pydantic import TypeAdapter
from struct_core.elements import (
    BeamElement,
    Element,
    SpringElement,
    TrussElement,
)
from struct_core.registry import ElementRegistry


def test_truss_element():
    elem = TrussElement(id=1, start_node="N1", end_node="N2", material_id="Mat1", section_id="Sec1")
    assert elem.id == 1
    assert elem.type == "truss"
    assert elem.start_node == "N1"
    assert elem.end_node == "N2"


def test_beam_element_with_releases():
    elem = BeamElement(
        id="B1",
        start_node=1,
        end_node=2,
        material_id="Steel",
        section_id="Rect",
        release_j=[False, False, True],  # Moment hinge at node j
    )
    assert elem.id == "B1"
    assert elem.type == "beam"
    assert elem.release_j == [False, False, True]


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
        "material_id": "M1",
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
