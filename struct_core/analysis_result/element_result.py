"""
Element result schemas for internal forces, moments, stresses, and strains.
"""

from typing import List, Optional
from pydantic import AliasChoices, Field
from ..base import BaseSchemaModel, ElementId


class BeamSectionForce(BaseSchemaModel):
    """
    Internal force and moment values at a specific section/station along an element.
    Follows standard structural local axes:
    - 1: Longitudinal centroidal axis (axial force P, torsion T)
    - 2: Transverse axis (shear V2, bending moment M2)
    - 3: Out-of-plane / transverse axis (shear V3, bending moment M3)
    """
    station: float = Field(default=0.0, description="Normalized or absolute position along element (0.0 to L or 0.0 to 1.0)")
    P: float = Field(default=0.0, description="Axial force along local 1-axis", validation_alias=AliasChoices("P", "p", "f1", "fx"))
    V2: float = Field(default=0.0, description="Shear force along local 2-axis", validation_alias=AliasChoices("V2", "v2", "Vy", "vy", "f2", "fy"))
    V3: float = Field(default=0.0, description="Shear force along local 3-axis", validation_alias=AliasChoices("V3", "v3", "Vz", "vz", "f3", "fz"))
    T: float = Field(default=0.0, description="Torsional moment about local 1-axis", validation_alias=AliasChoices("T", "t", "m1", "mx"))
    M2: float = Field(default=0.0, description="Bending moment about local 2-axis", validation_alias=AliasChoices("M2", "m2", "My", "my"))
    M3: float = Field(default=0.0, description="Bending moment about local 3-axis", validation_alias=AliasChoices("M3", "m3", "Mz", "mz", "m"))

    @property
    def Vy(self) -> float:
        return self.V2

    @property
    def Vz(self) -> float:
        return self.V3

    @property
    def My(self) -> float:
        return self.M2

    @property
    def Mz(self) -> float:
        return self.M3


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
