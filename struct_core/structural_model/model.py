"""
Root StructuralModel container holding nodes, elements, materials, sections, supports, loads, and analysis cases.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import Field
from ..base import BaseSchemaModel
from ..metadata import Metadata
from ..units import Units, parse_units
from .analysis import AnalysisCase
from .elements import Element
from .loads import AreaLoad, GroundMotion, LoadCase, LoadCombination, MassSource
from .materials import Material
from .nodes import Node
from .sections import Section
from .supports import Support


class StructuralModel(BaseSchemaModel):
    """
    Main structural model container holding physical, material, boundary condition, and loading data.
    """
    metadata: Metadata = Field(default_factory=Metadata, description="Model metadata and units")
    nodes: List[Node] = Field(default_factory=list, description="List of structural nodes")
    elements: List[Element] = Field(default_factory=list, description="List of structural elements")
    materials: List[Material] = Field(default_factory=list, description="List of material definitions")
    sections: List[Section] = Field(default_factory=list, description="List of cross-section definitions")
    supports: List[Support] = Field(default_factory=list, description="List of support boundary conditions")
    load_cases: List[LoadCase] = Field(default_factory=list, description="List of load cases")
    load_combinations: List[LoadCombination] = Field(default_factory=list, description="List of load combinations")
    area_loads: List[AreaLoad] = Field(default_factory=list, description="List of area/surface loads applied over floors/panels")
    story_elevations: List[float] = Field(default_factory=list, description="List of floor/story elevations (Z or Y coordinates)")
    ground_motions: List[GroundMotion] = Field(default_factory=list, description="List of ground motion records")
    analysis_cases: List[AnalysisCase] = Field(default_factory=list, description="List of analysis cases")
    mass_source: Optional[MassSource] = Field(default=None, description="Active mass source configuration for modal and dynamic analysis")
    mass_sources: List[MassSource] = Field(default_factory=list, description="List of defined mass sources")

    def __init__(self, **data: Any):
        units = data.pop("units", None)
        super().__init__(**data)
        if units is not None:
            self.units = units

    @property
    def units(self) -> Units:
        """Convenience accessor for model engineering units."""
        return self.metadata.units

    @units.setter
    def units(self, val: Union[Units, str, Dict[str, Any]]):
        if isinstance(val, (str, dict)):
            self.metadata.units = parse_units(val)
        elif isinstance(val, Units):
            self.metadata.units = val
        else:
            raise TypeError(f"Expected Units, str, or dict, got {type(val).__name__}")
