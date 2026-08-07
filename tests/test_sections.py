"""
Unit tests for cross-section schemas.
"""

import pytest
from pydantic import TypeAdapter, ValidationError
from struct_core.structural_model.sections import (
    CircularSection,
    GeneralSection,
    RectangularSection,
    Section,
)


def test_rectangular_section():
    sec = RectangularSection(id="R1", b=0.3, h=0.6)
    assert sec.id == "R1"
    assert sec.type == "rectangular"
    assert sec.b == 0.3
    assert sec.h == 0.6


def test_circular_section():
    sec = CircularSection(id="C1", d=0.4)
    assert sec.id == "C1"
    assert sec.type == "circular"
    assert sec.d == 0.4


def test_general_section():
    sec = GeneralSection(id="G1", A=0.05, Iz=0.001)
    assert sec.id == "G1"
    assert sec.type == "general"
    assert sec.A == 0.05
    assert sec.Iz == 0.001


def test_invalid_dimensions():
    with pytest.raises(ValidationError):
        RectangularSection(id="R1", b=-0.3, h=0.6)


def test_section_polymorphic_parsing():
    adapter = TypeAdapter(Section)

    data_rect = {"type": "rectangular", "id": "SEC1", "b": 0.25, "h": 0.5}
    parsed = adapter.validate_python(data_rect)
    assert isinstance(parsed, RectangularSection)
    assert parsed.b == 0.25
