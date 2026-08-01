"""
Unit tests for serialization functions.
"""

import tempfile
from pathlib import Path
from struct_core.elements import BeamElement
from struct_core.materials import ElasticMaterial
from struct_core.model import StructuralModel
from struct_core.nodes import Node
from struct_core.project import Project
from struct_core.sections import RectangularSection
from struct_core.serialization import from_dict, from_json, load_json, save_json, to_dict, to_json


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
        sections=[RectangularSection(id="BeamSec", b=0.3, h=0.5)],
        elements=[BeamElement(id=1, start_node=1, end_node=2, material_id="Steel", section_id="BeamSec")],
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
