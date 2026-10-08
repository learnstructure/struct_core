"""
Cross-section schemas for geometric and explicit general sections.
"""

import math
from typing import Annotated, Literal, Optional, Union
from pydantic import AliasChoices, Field
from ..base import BaseSchemaModel, SectionId


class BaseSection(BaseSchemaModel):
    """
    Base class for all cross-section definitions.
    """
    id: SectionId = Field(description="Unique section identifier")
    name: Optional[str] = Field(default=None, description="Human-readable section name (e.g. 'W14x90')")


class RectangularSection(BaseSection):
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


class CircularSection(BaseSection):
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

# Backward-compatible aliases
BaseSectionSchema = BaseSection
RectangularSectionSchema = RectangularSection
CircularSectionSchema = CircularSection
GeneralSectionSchema = GeneralSection
SectionSchema = Section
