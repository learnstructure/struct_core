"""
Cross-section schemas for geometric and explicit general sections.

A section is the complete definition of a member cross-section: its geometry and its material (``material_id``), as
in ETABS and SAP2000. Elements reference only a section, so the same shape in two materials is two sections.
Rectangular and circular sections may be reinforced concrete: they then also name their reinforcing-bar materials
and clear cover. Lengths are in the model length unit.
"""

import math
from typing import Annotated, Any, Literal, Optional, Union
from pydantic import AliasChoices, Field, model_validator
from ..base import BaseSchemaModel, MaterialId, SectionId


class BaseSection(BaseSchemaModel):
    """
    Base class for all cross-section definitions.
    """
    id: SectionId = Field(description="Unique section identifier")
    name: Optional[str] = Field(default=None, description="Human-readable section name (e.g. 'W14x90')")
    material_id: MaterialId = Field(description="Material of the section (for reinforced concrete, its concrete)")


class SolidSection(BaseSection):
    """
    Solid cross-section that may be reinforced concrete. For a concrete section, the reinforcement fields name the
    longitudinal and transverse bar materials (``RebarMaterial``) and the clear cover; design reads them from here.
    """
    rebar_material_id: Optional[MaterialId] = Field(
        default=None, description="Longitudinal reinforcing-bar material (RebarMaterial; fy)"
    )
    transverse_rebar_material_id: Optional[MaterialId] = Field(
        default=None, description="Transverse reinforcement material: stirrups, ties, hoops (RebarMaterial; fyt)"
    )
    cover: Optional[float] = Field(
        default=None, gt=0.0, description="Clear cover to the outermost (transverse) reinforcement, model length unit"
    )


class RectangularSection(SolidSection):
    """
    Geometric rectangular cross-section definition.
    Stores pure geometric parameters (b, h):
    - b: section width along local 3-axis (flange/transverse dimension)
    - h: section depth/height along local 2-axis (web dimension)
    """
    type: Literal["rectangular"] = "rectangular"
    b: float = Field(gt=0.0, description="Section width along local 3-axis")
    h: float = Field(gt=0.0, description="Section depth/height along local 2-axis")

    @property
    def As2(self) -> float:
        """Effective shear area along local 2-axis (5/6 * b * h for solid rectangle)."""
        return (5.0 / 6.0) * (self.b * self.h)

    @property
    def As3(self) -> float:
        """Effective shear area along local 3-axis (5/6 * b * h for solid rectangle)."""
        return (5.0 / 6.0) * (self.b * self.h)


class CircularSection(SolidSection):
    """
    Geometric circular cross-section definition.
    Stores pure geometric parameter (d).
    """
    type: Literal["circular"] = "circular"
    d: float = Field(gt=0.0, description="Section diameter")

    @property
    def As2(self) -> float:
        """Effective shear area along local 2-axis (0.9 * A for solid circle)."""
        return 0.9 * (math.pi * (self.d / 2.0) ** 2)

    @property
    def As3(self) -> float:
        """Effective shear area along local 3-axis (0.9 * A for solid circle)."""
        return 0.9 * (math.pi * (self.d / 2.0) ** 2)


class GeneralSection(BaseSection):
    """
    Explicit numerical section definition storing pre-computed properties:
    - I3: second moment of area about local 3-axis (major flexural axis)
    - I2: second moment of area about local 2-axis (minor flexural axis)
    - J: torsional constant about local 1-axis
    - As2: effective shear area along local 2-axis (transverse shear in 1-2 plane)
    - As3: effective shear area along local 3-axis (transverse shear in 1-3 plane)
    """
    type: Literal["general"] = "general"
    A: float = Field(gt=0.0, description="Cross-sectional area")
    I3: float = Field(gt=0.0, description="Second moment of area about local 3-axis", validation_alias=AliasChoices("I3", "Iz", "i3", "iz"))
    I2: float = Field(default=0.0, ge=0.0, description="Second moment of area about local 2-axis", validation_alias=AliasChoices("I2", "Iy", "i2", "iy"))
    J: float = Field(default=0.0, ge=0.0, description="Torsional constant about local 1-axis", validation_alias=AliasChoices("J", "j"))
    As2: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Effective shear area along local 2-axis (transverse shear in 1-2 plane)",
        validation_alias=AliasChoices("As2", "as2", "Ay", "ay", "AS2"),
    )
    As3: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Effective shear area along local 3-axis (transverse shear in 1-3 plane)",
        validation_alias=AliasChoices("As3", "as3", "Az", "az", "AS3"),
    )


# Discriminated union for section deserialization
Section = Annotated[
    Union[RectangularSection, CircularSection, GeneralSection],
    Field(discriminator="type")
]


