"""
Cross-section schemas for geometric and explicit general sections.
"""

from typing import Annotated, Literal, Optional, Union
from pydantic import Field
from .base import BaseSchemaModel, SectionId


class BaseSection(BaseSchemaModel):
    """
    Base class for all cross-section definitions.
    """
    id: SectionId = Field(description="Unique section identifier")
    name: Optional[str] = Field(default=None, description="Human-readable section name (e.g. 'W14x90')")


class RectangularSection(BaseSection):
    """
    Geometric rectangular cross-section definition.
    Stores pure geometric parameters (b, h).
    """
    type: Literal["rectangular"] = "rectangular"
    b: float = Field(gt=0.0, description="Section width along local y-axis")
    h: float = Field(gt=0.0, description="Section depth/height along local z-axis")


class CircularSection(BaseSection):
    """
    Geometric circular cross-section definition.
    Stores pure geometric parameter (d).
    """
    type: Literal["circular"] = "circular"
    d: float = Field(gt=0.0, description="Section diameter")


class GeneralSection(BaseSection):
    """
    Explicit numerical section definition storing pre-computed properties.
    """
    type: Literal["general"] = "general"
    A: float = Field(gt=0.0, description="Cross-sectional area")
    Iz: float = Field(gt=0.0, description="Second moment of area about local z-axis")
    Iy: float = Field(default=0.0, ge=0.0, description="Second moment of area about local y-axis")
    J: float = Field(default=0.0, ge=0.0, description="Torsional constant")


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
