"""
Unit tests for structural validation rules.
"""

import pytest
from struct_core.elements import BeamElement
from struct_core.loads import DistributedLoad, LoadCase, PointLoad
from struct_core.materials import ElasticMaterial
from struct_core.model import StructuralModel
from struct_core.nodes import Node
from struct_core.sections import RectangularSection
from struct_core.supports import Support
from struct_core.validation import StructuralValidationError, validate_structural_model


def test_valid_model():
    model = StructuralModel(
        nodes=[Node(id=1, x=0.0, y=0.0), Node(id=2, x=0.0, y=3.0)],
        materials=[ElasticMaterial(id="M1", E=200e9)],
        sections=[RectangularSection(id="S1", b=0.3, h=0.3)],
        elements=[BeamElement(id=1, start_node=1, end_node=2, material_id="M1", section_id="S1")],
        supports=[Support.fixed(node_id=1)],
        load_cases=[LoadCase(id="DL", point_loads=[PointLoad(node_id=2, fy=-10.0)])],
    )
    errors = validate_structural_model(model, raise_error=True)
    assert len(errors) == 0


def test_duplicate_node_ids():
    model = StructuralModel(
        nodes=[Node(id=1, x=0.0, y=0.0), Node(id=1, x=1.0, y=1.0)],
    )
    with pytest.raises(StructuralValidationError) as excinfo:
        validate_structural_model(model)
    assert "Duplicate Node ID found: '1'" in str(excinfo.value)


def test_missing_node_reference():
    model = StructuralModel(
        nodes=[Node(id=1, x=0.0, y=0.0)],
        materials=[ElasticMaterial(id="M1", E=200e9)],
        sections=[RectangularSection(id="S1", b=0.3, h=0.3)],
        elements=[BeamElement(id=1, start_node=1, end_node=99, material_id="M1", section_id="S1")],
    )
    errors = validate_structural_model(model, raise_error=False)
    assert any("missing end_node '99'" in e for e in errors)


def test_missing_material_or_section_reference():
    model = StructuralModel(
        nodes=[Node(id=1, x=0.0, y=0.0), Node(id=2, x=0.0, y=3.0)],
        elements=[BeamElement(id=1, start_node=1, end_node=2, material_id="MISSING_MAT", section_id="MISSING_SEC")],
    )
    errors = validate_structural_model(model, raise_error=False)
    assert any("missing material_id 'MISSING_MAT'" in e for e in errors)
    assert any("missing section_id 'MISSING_SEC'" in e for e in errors)


def test_zero_length_element():
    model = StructuralModel(
        nodes=[Node(id=1, x=2.0, y=5.0), Node(id=2, x=2.0, y=5.0)],
        materials=[ElasticMaterial(id="M1", E=200e9)],
        sections=[RectangularSection(id="S1", b=0.3, h=0.3)],
        elements=[BeamElement(id=1, start_node=1, end_node=2, material_id="M1", section_id="S1")],
    )
    errors = validate_structural_model(model, raise_error=False)
    assert any("zero length" in e for e in errors)


def test_missing_load_references():
    model = StructuralModel(
        nodes=[Node(id=1, x=0.0, y=0.0)],
        load_cases=[
            LoadCase(
                id="DL",
                point_loads=[PointLoad(node_id=99, fy=-10.0)],
                element_loads=[DistributedLoad(element_id=88, wy=-5.0)],
            )
        ],
    )
    errors = validate_structural_model(model, raise_error=False)
    assert any("missing node_id '99'" in e for e in errors)
    assert any("missing element_id '88'" in e for e in errors)
