"""
Node result schemas for displacements, rotations, and reactions.
"""

from typing import Optional
from pydantic import Field
from ..base import BaseSchemaModel, NodeId


class NodeDisplacement(BaseSchemaModel):
    """
    Nodal displacement and rotation values [ux, uy, uz, rx, ry, rz].
    """
    ux: float = Field(default=0.0, description="Translation along X-axis")
    uy: float = Field(default=0.0, description="Translation along Y-axis")
    uz: float = Field(default=0.0, description="Translation along Z-axis")
    rx: float = Field(default=0.0, description="Rotation about X-axis")
    ry: float = Field(default=0.0, description="Rotation about Y-axis")
    rz: float = Field(default=0.0, description="Rotation about Z-axis")


class NodeReaction(BaseSchemaModel):
    """
    Nodal support reaction forces and moments [fx, fy, fz, mx, my, mz].
    """
    fx: float = Field(default=0.0, description="Reaction force along X-axis")
    fy: float = Field(default=0.0, description="Reaction force along Y-axis")
    fz: float = Field(default=0.0, description="Reaction force along Z-axis")
    mx: float = Field(default=0.0, description="Reaction moment about X-axis")
    my: float = Field(default=0.0, description="Reaction moment about Y-axis")
    mz: float = Field(default=0.0, description="Reaction moment about Z-axis")


class NodeResult(BaseSchemaModel):
    """
    Composite result at a node combining displacements and support reactions.
    """
    node_id: NodeId = Field(description="Target node ID")
    displacement: NodeDisplacement = Field(default_factory=NodeDisplacement, description="Nodal displacement vector")
    reaction: Optional[NodeReaction] = Field(default=None, description="Nodal reaction force vector (if supported)")
