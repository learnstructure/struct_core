"""
Unit tests for serialization functions.
"""

import tempfile
from pathlib import Path
from struct_core.project import Project
from struct_core.serialization import from_dict, from_json, load_json, save_json, to_dict, to_json
from struct_core.structural_model import (
    BeamElement,
    ElasticMaterial,
    Node,
    RectangularSection,
    StructuralModel,
)


def test_dict_serialization():
    proj = Project()
    proj.metadata.title = "Portal Frame Project"
    proj.model.nodes.extend([Node(id=1, x=0.0, y=0.0), Node(id=2, x=0.0, y=4.0)])
    proj.model.materials.append(ElasticMaterial(id="M1", E=210e9))

    data = to_dict(proj)
    assert isinstance(data, dict)
    assert data["metadata"]["title"] == "Portal Frame Project"
    assert len(data["model"]["nodes"]) == 2

    reconstructed = from_dict(Project, data)
    assert reconstructed.metadata.title == proj.metadata.title
    assert len(reconstructed.model.nodes) == 2


def test_json_serialization():
    model = StructuralModel(
        nodes=[Node(id=1, x=0.0, y=0.0), Node(id=2, x=5.0, y=0.0)],
        materials=[ElasticMaterial(id="Steel", E=200e9)],
        sections=[RectangularSection(id="BeamSec", b=0.3, h=0.5, material_id="Steel")],
        elements=[BeamElement(id=1, start_node=1, end_node=2, section_id="BeamSec")],
    )

    json_str = to_json(model)
    assert isinstance(json_str, str)
    assert '"start_node": 1' in json_str or '"start_node":1' in json_str

    reconstructed = from_json(StructuralModel, json_str)
    assert len(reconstructed.nodes) == 2
    assert reconstructed.elements[0].section_id == "BeamSec"


def test_file_io_serialization():
    proj = Project()
    proj.metadata.title = "File IO Test"
    proj.model.nodes.append(Node(id=1, x=1.0, y=2.0))

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = str(Path(tmpdir) / "project.json")
        save_json(proj, file_path)

        loaded_proj = load_json(Project, file_path)
        assert loaded_proj.metadata.title == "File IO Test"
        assert loaded_proj.model.nodes[0].x == 1.0


def test_design_inputs_roundtrip():
    from struct_core import AppliedDefault, ConcreteMaterial, DesignInputs, DesignResult, RebarMaterial

    proj = Project(units="kN, m")
    proj.design_results["D"] = DesignResult(design_code="ACI 318-25", inputs=DesignInputs(
        design_code="ACI 318-25",
        materials=[ConcreteMaterial(id="C4000", fc=27_600.0, E=24.9e6), RebarMaterial(id="G60", fy=414_000.0, E=2.0e8)],
        sections=[RectangularSection(id="COL", b=0.45, h=0.45, material_id="C4000", rebar_material_id="G60", cover=0.04)],
        allowable_bearing_pressure=150.0,
        defaults_applied=[AppliedDefault(name="allowable_bearing_pressure", value=150.0, unit="kPa",
                                         source="tool default", applies_to=None)],
    ))
    back = Project.model_validate_json(proj.model_dump_json()).design_results["D"].inputs
    assert [type(m).__name__ for m in back.materials] == ["ConcreteMaterial", "RebarMaterial"]
    assert back.sections[0].rebar_material_id == "G60"
    assert back.defaults_applied[0].value == 150.0
