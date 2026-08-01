"""
Element schemas representing structural members (Truss, Beam, Spring).
"""

from typing import Annotated, Literal, Optional, Union
from pydantic import Field
from .base import BaseSchemaModel, ElementId, MaterialId, NodeId, SectionId


class BaseElement(BaseSchemaModel):
    """
    Base class for all structural finite elements.
    """
    id: ElementId = Field(description="Unique element identifier")
    start_node: NodeId = Field(description="Node ID at element start (i-node)")
    end_node: NodeId = Field(description="Node ID at element end (j-node)")
    name: Optional[str] = Field(default=None, description="Human-readable element name/tag")


class TrussElement(BaseElement):
    """
    2D/3D Truss element schema (axial forces only).
    """
    type: Literal["truss"] = "truss"
    material_id: MaterialId = Field(description="Associated material ID")
    section_id: SectionId = Field(description="Associated section ID")
    is_nonlinear: bool = Field(default=False, description="Flag for geometric/material nonlinearity")


class BeamElement(BaseElement):
    """
    2D/3D Frame beam-column element schema with optional end releases (hinges).
    """
    type: Literal["beam"] = "beam"
    material_id: MaterialId = Field(description="Associated material ID")
    section_id: SectionId = Field(description="Associated section ID")
    release_i: list[bool] = Field(
        default_factory=lambda: [False, False, False],
        description="End release flags at i-node [ux, uy, rz]"
    )
    release_j: list[bool] = Field(
        default_factory=lambda: [False, False, False],
        description="End release flags at j-node [ux, uy, rz]"
    )
    is_nonlinear: bool = Field(default=False, description="Flag for geometric/material nonlinearity")


class SpringElement(BaseElement):
    """
    Spring element schema specifying directional stiffnesses.
    """
    type: Literal["spring"] = "spring"
    kx: float = Field(default=0.0, ge=0.0, description="Translational stiffness along x-axis")
    ky: float = Field(default=0.0, ge=0.0, description="Translational stiffness along y-axis")
    kz: float = Field(default=0.0, ge=0.0, description="Rotational/z-axis stiffness")


# Discriminated union for polymorphic element parsing
Element = Annotated[
    Union[TrussElement, BeamElement, SpringElement],
    Field(discriminator="type")
]

# Backward-compatible aliases
BaseElementSchema = BaseElement
TrussElementSchema = TrussElement
BeamElementSchema = BeamElement
SpringElementSchema = SpringElement
ElementSchema = Element
