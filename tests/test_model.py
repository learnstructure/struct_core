"""
Unit tests for StructuralModel and Project containers.
"""

from struct_core.analysis import LinearStaticAnalysis
from struct_core.elements import BeamElement
from struct_core.loads import LoadCase, PointLoad
from struct_core.materials import ElasticMaterial
from struct_core.model import StructuralModel
from struct_core.nodes import Node
from struct_core.project import Project
from struct_core.sections import RectangularSection
from struct_core.supports import Support


def test_structural_model_building():
    model = StructuralModel()

    # Add Nodes
    n1 = Node(id=1, x=0.0, y=0.0)
    n2 = Node(id=2, x=0.0, y=3.0)
    model.nodes.extend([n1, n2])

    # Add Material and Section
    mat = ElasticMaterial(id="Steel", E=200e9)
    sec = RectangularSection(id="ColSec", b=0.3, h=0.3)
    model.materials.append(mat)
    model.sections.append(sec)

    # Add Element
    elem = BeamElement(id=1, start_node=1, end_node=2, material_id="Steel", section_id="ColSec")
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
