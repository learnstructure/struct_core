"""
Modal analysis result schemas for mode shapes, periods, frequencies, and mass participation.
"""

from typing import Dict, List
from pydantic import Field
from ..base import BaseSchemaModel, NodeId
from .node_result import NodeDisplacement


class ModeShape(BaseSchemaModel):
    """
    Mode shape definition for a single natural frequency.
    """
    mode_number: int = Field(gt=0, description="Mode number (1, 2, 3...)")
    period: float = Field(gt=0.0, description="Natural period in seconds")
    frequency: float = Field(gt=0.0, description="Natural frequency in Hz")
    circular_frequency: float = Field(gt=0.0, description="Circular frequency omega in rad/s")
    mass_participation_x: float = Field(default=0.0, ge=0.0, le=1.0, description="Mass participation ratio along X")
    mass_participation_y: float = Field(default=0.0, ge=0.0, le=1.0, description="Mass participation ratio along Y")
    displacements: Dict[NodeId, NodeDisplacement] = Field(default_factory=dict, description="Nodal mode shape displacements")


class ModalResult(BaseSchemaModel):
    """
    Composite result container for modal analysis outputs.
    """
    modes: List[ModeShape] = Field(default_factory=list, description="List of calculated mode shapes")
