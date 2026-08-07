"""
Root StructuralModel container holding nodes, elements, materials, sections, supports, loads, and analysis cases.
"""

from typing import List
from pydantic import Field
from ..base import BaseSchemaModel
from .analysis import AnalysisCase
from .elements import Element
from .loads import GroundMotion, LoadCase, LoadCombination
from .materials import Material
from .nodes import Node
from .sections import Section
from .supports import Support


class StructuralModel(BaseSchemaModel):
    """
    Main structural model container holding physical, material, boundary condition, and loading data.
    """
    nodes: List[Node] = Field(default_factory=list, description="List of structural nodes")
    elements: List[Element] = Field(default_factory=list, description="List of structural elements")
    materials: List[Material] = Field(default_factory=list, description="List of material definitions")
    sections: List[Section] = Field(default_factory=list, description="List of cross-section definitions")
    supports: List[Support] = Field(default_factory=list, description="List of support boundary conditions")
    load_cases: List[LoadCase] = Field(default_factory=list, description="List of load cases")
    load_combinations: List[LoadCombination] = Field(default_factory=list, description="List of load combinations")
    ground_motions: List[GroundMotion] = Field(default_factory=list, description="List of ground motion records")
    analysis_cases: List[AnalysisCase] = Field(default_factory=list, description="List of analysis cases")
