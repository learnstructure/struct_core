"""Tests for ObjectGroup (StructuralModel.groups) and load_type='other'."""

import pytest
from pydantic import ValidationError

from struct_core import (
    BeamElement,
    ConcreteMaterial,
    LoadCase,
    Node,
    ObjectGroup,
    Project,
    RectangularSection,
    ShellElement,
    ShellSection,
    StructuralModel,
    StructuralValidationError,
    Support,
    VALID_LOAD_TYPES,
    classify_load_case,
    validate_structural_model,
)


def _sample_model() -> StructuralModel:
    return StructuralModel(
        units="kN, m",
        nodes=[
            Node(id="1", x=0.0, y=0.0, z=0.0),
            Node(id="2", x=0.0, y=0.0, z=3.0),
            Node(id="3", x=4.0, y=0.0, z=3.0),
            Node(id="4", x=4.0, y=4.0, z=3.0),
            Node(id="5", x=0.0, y=4.0, z=3.0),
        ],
        materials=[ConcreteMaterial(id="C30", E=25e6, fc=30e3, unit_weight=24.0)],
        sections=[RectangularSection(id="COL", material_id="C30", b=0.4, h=0.4)],
        elements=[BeamElement(id="C1", start_node="1", end_node="2", section_id="COL")],
        shell_sections=[ShellSection(id="S200", material_id="C30", thickness=0.2)],
        shell_elements=[ShellElement(id="A1", node_ids=["2", "3", "4", "5"], section_id="S200")],
        supports=[Support.fixed_3d("1")],
        groups=[
            ObjectGroup(id="roof", node_ids=["2", "3"], shell_element_ids=["A1"]),
            ObjectGroup(id="columns", element_ids=["C1"]),
        ],
    )


def test_object_group_schema_lookup_and_json_roundtrip():
    model = _sample_model()
    assert validate_structural_model(model, raise_error=False) == []
    assert model.get_group("roof") == ObjectGroup(id="roof", node_ids=["2", "3"], shell_element_ids=["A1"])
    assert model.get_group("missing") is None

    reloaded = StructuralModel.model_validate_json(model.model_dump_json())
    assert reloaded.groups == model.groups

    project = Project(model=model, units="kN, m")
    assert project.groups == model.groups
    project.groups = [ObjectGroup(id="base", node_ids=["1"])]
    assert [g.id for g in project.model.groups] == ["base"]


@pytest.mark.parametrize("bad_id", ["", "   "])
def test_object_group_rejects_blank_id(bad_id):
    with pytest.raises(ValidationError):
        ObjectGroup(id=bad_id)


def test_validate_structural_model_checks_group_duplicates_and_references():
    model = _sample_model()
    model.groups.append(ObjectGroup(id="roof", node_ids=["999"]))
    model.groups.append(
        ObjectGroup(
            id="bad_refs",
            node_ids=["1", "1"],
            element_ids=["C1", "C1", "NO_EL"],
            shell_element_ids=["A1", "A1", "NO_SH"],
        )
    )

    errors = validate_structural_model(model, raise_error=False)
    text = "\n".join(errors)
    assert "Duplicate group ID found: 'roof'" in text
    assert "Group 'roof' references missing node(s) ['999']" in text
    assert "Group 'bad_refs' contains duplicate node ID(s) ['1']" in text
    assert "Group 'bad_refs' contains duplicate element ID(s) ['C1']" in text
    assert "Group 'bad_refs' references missing element(s) ['NO_EL']" in text
    assert "Group 'bad_refs' contains duplicate shell element ID(s) ['A1']" in text
    assert "Group 'bad_refs' references missing shell element(s) ['NO_SH']" in text

    with pytest.raises(StructuralValidationError):
        validate_structural_model(model)


def test_load_type_other_is_valid_and_classified_explicitly():
    assert "other" in VALID_LOAD_TYPES
    lc = LoadCase(id="DEAD_TEST", load_type="Other")
    assert lc.load_type == "other"
    assert classify_load_case(lc) == "other"

    untyped = LoadCase(id="MYSTERY_CASE")
    assert untyped.load_type is None
    assert classify_load_case(untyped, allow_unknown=True) == "unknown"
    with pytest.raises(ValueError, match="Unable to determine load type"):
        classify_load_case(untyped)
