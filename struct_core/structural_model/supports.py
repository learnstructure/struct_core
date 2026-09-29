"""
Boundary conditions and support schemas.
"""

from typing import Optional
from pydantic import Field
from ..base import BaseSchemaModel, NodeId


class Support(BaseSchemaModel):
    """
    Nodal support boundary condition specification.
    Stores fixity flags and optional elastic spring stiffnesses for all 6 degrees of freedom
    [ux, uy, uz, rx, ry, rz].  The 2D subset [ux, uy, rz] defaults to the same behaviour as before.
    """
    node_id: NodeId = Field(description="Target node ID")
    ux: bool = Field(default=False, description="Whether translation along X is fixed")
    uy: bool = Field(default=False, description="Whether translation along Y is fixed")
    uz: bool = Field(default=False, description="Whether translation along Z is fixed")
    rx: bool = Field(default=False, description="Whether rotation about X is fixed")
    ry: bool = Field(default=False, description="Whether rotation about Y is fixed")
    rz: bool = Field(default=False, description="Whether rotation about Z is fixed")

    kx: float = Field(default=0.0, ge=0.0, description="Elastic support stiffness along X")
    ky: float = Field(default=0.0, ge=0.0, description="Elastic support stiffness along Y")
    kz: float = Field(default=0.0, ge=0.0, description="Elastic support stiffness along Z")
    krx: float = Field(default=0.0, ge=0.0, description="Elastic rotational support stiffness about X")
    kry: float = Field(default=0.0, ge=0.0, description="Elastic rotational support stiffness about Y")
    krz: float = Field(default=0.0, ge=0.0, description="Elastic rotational support stiffness about Z")

    name: Optional[str] = Field(default=None, description="Support name or tag (e.g. 'Pinned Support')")

    @classmethod
    def pinned(cls, node_id: NodeId, name: Optional[str] = None) -> "Support":
        """Factory method for a 2D pinned support [ux=True, uy=True, rz=False]."""
        return cls(node_id=node_id, ux=True, uy=True, rz=False, name=name or "Pinned")

    @classmethod
    def pinned_3d(cls, node_id: NodeId, name: Optional[str] = None) -> "Support":
        """Factory method for a 3D pinned support [ux, uy, uz=True; rx, ry, rz=False]."""
        return cls(node_id=node_id, ux=True, uy=True, uz=True, name=name or "Pinned-3D")

    @classmethod
    def fixed(cls, node_id: NodeId, name: Optional[str] = None) -> "Support":
        """Factory method for a 2D fixed support [ux=True, uy=True, rz=True]."""
        return cls(node_id=node_id, ux=True, uy=True, rz=True, name=name or "Fixed")

    @classmethod
    def fixed_3d(cls, node_id: NodeId, name: Optional[str] = None) -> "Support":
        """Factory method for a 3D fully fixed support (all 6 DOFs)."""
        return cls(node_id=node_id, ux=True, uy=True, uz=True, rx=True, ry=True, rz=True, name=name or "Fixed-3D")

    @classmethod
    def roller_x(cls, node_id: NodeId, name: Optional[str] = None) -> "Support":
        """Factory method for a roller support allowing X motion [ux=False, uy=True, rz=False]."""
        return cls(node_id=node_id, ux=False, uy=True, rz=False, name=name or "Roller-X")

    @classmethod
    def roller_y(cls, node_id: NodeId, name: Optional[str] = None) -> "Support":
        """Factory method for a roller support allowing Y motion [ux=True, uy=False, rz=False]."""
        return cls(node_id=node_id, ux=True, uy=False, rz=False, name=name or "Roller-Y")


# Backward-compatible alias
SupportSchema = Support
