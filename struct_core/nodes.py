"""
Node schema representing grid points in a 2D or 3D structural model.
"""

from pydantic import Field
from .base import BaseSchemaModel, NodeId


class Node(BaseSchemaModel):
    """
    Represents a nodal grid point in a structural model.
    """
    id: NodeId = Field(description="Unique node identifier")
    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")
    z: float = Field(default=0.0, description="Z coordinate (defaults to 0.0 for 2D models)")
    mass: float = Field(default=0.0, ge=0.0, description="Translational lumped mass")
    inertia: float = Field(default=0.0, ge=0.0, description="Rotational lumped inertia")


# Backward-compatible alias
NodeSchema = Node
