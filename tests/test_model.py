"""
Unit tests for StructuralModel and Project containers.
"""

from struct_core.project import Project
from struct_core.structural_model import (
    BeamElement,
    ElasticMaterial,
    LinearStaticAnalysis,
    LoadCase,
    Node,
    PointLoad,
    RectangularSection,
    StructuralModel,
    Support,
)


def test_structural_model_building():
    model = StructuralModel()

    # Add Nodes
    n1 = Node(id=1, x=0.0, y=0.0)
    n2 = Node(id=2, x=0.0, y=3.0)
    model.nodes.extend([n1, n2])

    # Add Material and Section
    mat = ElasticMaterial(id="Steel", E=200e9)
    sec = RectangularSection(id="ColSec", b=0.3, h=0.3, material_id="Steel")
    model.materials.append(mat)
    model.sections.append(sec)

    # Add Element
    elem = BeamElement(id=1, start_node=1, end_node=2, section_id="ColSec")
    model.elements.append(elem)

    # Add Support
    model.supports.append(Support.fixed(node_id=1))

    # Add Load
    lc = LoadCase(id="DL", point_loads=[PointLoad(node_id=2, fy=-50.0)])
    model.load_cases.append(lc)

    # Add Analysis Case
    model.analysis_cases.append(LinearStaticAnalysis(id="A1", load_case_id="DL"))

    assert len(model.nodes) == 2
    assert len(model.elements) == 1
    assert len(model.supports) == 1
    assert len(model.load_cases) == 1
    assert len(model.analysis_cases) == 1


def test_project_container():
    proj = Project()
    proj.metadata.title = "Frame Project"
    proj.model.nodes.append(Node(id=1, x=0.0, y=0.0))

    assert proj.metadata.title == "Frame Project"
    assert len(proj.model.nodes) == 1


def test_elements_resolve_their_section_and_material():
    from struct_core.structural_model import ConcreteMaterial, SpringElement
    model = StructuralModel(
        nodes=[Node(id=1, x=0.0, y=0.0), Node(id=2, x=0.0, y=3.0)],
        materials=[ConcreteMaterial(id="C4000", fc=27_600.0, E=24.9e6)],
        sections=[RectangularSection(id="COL", b=0.4, h=0.4, material_id="C4000")],
        elements=[BeamElement(id=1, start_node=1, end_node=2, section_id="COL"),
                  SpringElement(id="K", start_node=1, end_node=2, kx=1.0)],
    )
    assert model.section_of(1).id == "COL"
    assert model.material_of(model.elements[0]).id == "C4000"
    assert model.material_of(model.sections[0]).id == "C4000"
    assert model.section_of("K") is None and model.material_of("K") is None
    assert model.get_material("missing") is None and model.get_section("missing") is None


def test_legacy_element_materials_move_to_sections():
    """Models saved before sections owned their material kept material_id on each element."""
    legacy = {
        "metadata": {"schema_version": "1.0.0", "title": "old frame"},
        "nodes": [{"id": 1, "x": 0, "y": 0}, {"id": 2, "x": 0, "y": 3}, {"id": 3, "x": 5, "y": 3}],
        "materials": [{"type": "elastic", "id": "C30", "E": 3.0e7}, {"type": "elastic", "id": "C40", "E": 3.3e7}],
        "sections": [{"type": "rectangular", "id": "COL", "b": 0.4, "h": 0.4},
                     {"type": "rectangular", "id": "BEAM", "b": 0.3, "h": 0.5}],
        "elements": [
            {"type": "beam", "id": 1, "start_node": 1, "end_node": 2, "material_id": "C30", "section_id": "COL"},
            {"type": "beam", "id": 2, "start_node": 2, "end_node": 3, "material_id": "C40", "section_id": "COL"},
            {"type": "beam", "id": 3, "start_node": 1, "end_node": 3, "material_id": "C40", "section_id": "COL"},
            {"type": "truss", "id": 4, "start_node": 1, "end_node": 3, "material_id": "C30", "section_id": "BEAM"},
        ],
    }
    proj = Project.model_validate({"model": legacy})
    model = proj.model
    # COL keeps the material most of its elements used; the other material gets a copy of the section
    assert [(s.id, s.material_id, s.b) for s in model.sections] == [
        ("COL", "C40", 0.4), ("BEAM", "C30", 0.3), ("COL_C30", "C30", 0.4)]
    assert [(e.id, e.section_id) for e in model.elements] == [(1, "COL_C30"), (2, "COL"), (3, "COL"), (4, "BEAM")]
    assert [model.material_of(e).id for e in model.elements] == ["C30", "C40", "C40", "C30"]
    assert (proj.metadata.title, proj.metadata.schema_version) == ("old frame", "2.0.0")


def test_legacy_section_without_elements_takes_the_only_material():
    legacy = {"materials": [{"type": "elastic", "id": "M", "E": 2.0e8}],
              "sections": [{"type": "rectangular", "id": "UNUSED", "b": 0.3, "h": 0.3}],
              "nodes": [{"id": 1, "x": 0, "y": 0}, {"id": 2, "x": 1, "y": 0}],
              "elements": [{"type": "truss", "id": 1, "start_node": 1, "end_node": 2, "material_id": "M",
                            "section_id": "MISSING"}]}
    model = StructuralModel.model_validate(legacy)
    assert model.sections[0].material_id == "M"
    assert not hasattr(model.elements[0], "material_id")
