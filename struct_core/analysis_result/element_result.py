"""
Element result schemas for internal forces, moments, stresses, and strains.
"""

from typing import List, Optional
from pydantic import Field
from ..base import BaseSchemaModel, ElementId


class BeamSectionForce(BaseSchemaModel):
    """
    Internal force and moment values at a specific section/station along an element.
    """
    station: float = Field(default=0.0, description="Normalized or absolute position along element (0.0 to L or 0.0 to 1.0)")
    P: float = Field(default=0.0, description="Axial force (compression negative or positive per convention)")
    Vy: float = Field(default=0.0, description="Shear force along local y-axis")
    Vz: float = Field(default=0.0, description="Shear force along local z-axis")
    T: float = Field(default=0.0, description="Torsional moment")
    My: float = Field(default=0.0, description="Bending moment about local y-axis")
    Mz: float = Field(default=0.0, description="Bending moment about local z-axis")


class ElementForceResult(BaseSchemaModel):
    """
    Collection of internal force distributions along an element.
    """
    element_id: ElementId = Field(description="Target element ID")
    stations: List[BeamSectionForce] = Field(default_factory=list, description="Section force outputs along element length")


class ElementResult(BaseSchemaModel):
    """
    Composite element output result (forces, envelope, max/min stresses).
    """
    element_id: ElementId = Field(description="Target element ID")
    forces: List[BeamSectionForce] = Field(default_factory=list, description="Section force stations")
    max_axial: Optional[float] = Field(default=None, description="Maximum axial force")
    max_moment: Optional[float] = Field(default=None, description="Maximum bending moment")
    max_shear: Optional[float] = Field(default=None, description="Maximum shear force")
