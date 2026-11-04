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
    sec = RectangularSection(id="R1", material_id="M", b=0.3, h=0.6)
    assert sec.id == "R1"
    assert sec.type == "rectangular"
    assert sec.b == 0.3
    assert sec.h == 0.6


def test_circular_section():
    sec = CircularSection(id="C1", material_id="M", d=0.4)
    assert sec.id == "C1"
    assert sec.type == "circular"
    assert sec.d == 0.4


def test_general_section():
    sec = GeneralSection(id="G1", material_id="M", A=0.05, I3=0.001, I2=0.0005, J=0.0002)
    assert sec.id == "G1"
    assert sec.type == "general"
    assert sec.A == 0.05
    assert sec.I3 == 0.001
    assert sec.I2 == 0.0005
    assert sec.J == 0.0002


def test_invalid_dimensions():
    with pytest.raises(ValidationError):
        RectangularSection(id="R1", material_id="M", b=-0.3, h=0.6)


def test_section_polymorphic_parsing():
    adapter = TypeAdapter(Section)

    data_rect = {"type": "rectangular", "id": "SEC1", "material_id": "M", "b": 0.25, "h": 0.5}
    parsed = adapter.validate_python(data_rect)
    assert isinstance(parsed, RectangularSection)
    assert parsed.b == 0.25


def test_section_shear_areas():
    rect = RectangularSection(id="R1", material_id="M", b=0.2, h=0.4)
    assert pytest.approx(rect.As2, rel=1e-5) == (5.0 / 6.0) * (0.2 * 0.4)
    assert pytest.approx(rect.As3, rel=1e-5) == (5.0 / 6.0) * (0.2 * 0.4)

    circ = CircularSection(id="C1", material_id="M", d=0.5)
    import math
    expected_as = 0.9 * math.pi * 0.25**2
    assert pytest.approx(circ.As2, rel=1e-5) == expected_as
    assert pytest.approx(circ.As3, rel=1e-5) == expected_as

    gen = GeneralSection(id="G1", material_id="M", A=10.0, I3=100.0, As2=8.33, As3=7.5)
    assert gen.As2 == 8.33
    assert gen.As3 == 7.5

    # Test alias support
    gen_alias = GeneralSection(id="G2", material_id="M", A=10.0, I3=100.0, Ay=8.0, Az=7.0)
    assert gen_alias.As2 == 8.0
    assert gen_alias.As3 == 7.0



def test_sections_own_their_material_and_reinforcement():
    rc = RectangularSection(id="COL", b=0.45, h=0.45, material_id="C4000", rebar_material_id="G60",
                            transverse_rebar_material_id="G40", cover=0.04)
    assert (rc.material_id, rc.rebar_material_id, rc.transverse_rebar_material_id, rc.cover) == ("C4000", "G60", "G40", 0.04)
    plain = CircularSection(id="PIPE", d=0.3, material_id="Steel")
    assert plain.rebar_material_id is None and plain.cover is None  # reinforcement is optional
    with pytest.raises(ValidationError):
        RectangularSection(id="NoMaterial", b=0.3, h=0.3)  # every section names its material
    with pytest.raises(ValidationError):
        RectangularSection(id="BadCover", b=0.3, h=0.3, material_id="M", cover=0.0)
