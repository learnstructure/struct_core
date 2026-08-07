"""
Reinforcing steel bar, layer, and stirrup layout schemas.
"""

from typing import List, Optional
from pydantic import Field
from ..base import BaseSchemaModel


class Bar(BaseSchemaModel):
    """
    Specification of a single reinforcing steel bar or bundle of bars.
    """
    mark: str = Field(description="Unique bar designation mark (e.g. '1B1', 'T1')")
    size: int = Field(gt=0, description="US bar size number (e.g. 4 for #4, 8 for #8) or metric diameter in mm")
    count: int = Field(default=1, gt=0, description="Quantity count of identical bars")
    length: float = Field(gt=0.0, description="Cut length of the bar (in or mm)")
    weight: float = Field(default=0.0, ge=0.0, description="Total weight of bars (lbs or kg)")


class RebarLayer(BaseSchemaModel):
    """
    Layer of parallel longitudinal reinforcing bars at a specified cross-section depth.
    """
    depth: float = Field(ge=0.0, description="Depth from compression face to layer centroid")
    bars: List[Bar] = Field(default_factory=list, description="Bars in this layer")


class StirrupLayout(BaseSchemaModel):
    """
    Transverse tie / stirrup reinforcement zone along a member.
    """
    size: int = Field(gt=0, description="Stirrup bar size number (e.g. 3 for #3)")
    spacing: float = Field(gt=0.0, description="Stirrup center-to-center spacing along length")
    legs: int = Field(default=2, gt=0, description="Number of vertical stirrup legs (e.g. 2, 4)")
    start_zone: float = Field(default=0.0, ge=0.0, description="Start distance of stirrup zone from member end")
    end_zone: float = Field(gt=0.0, description="End distance of stirrup zone from member end")


class BarLayout(BaseSchemaModel):
    """
    Complete 3D cross-sectional and longitudinal reinforcement layout for a member.
    """
    top_layers: List[RebarLayer] = Field(default_factory=list, description="Top flexural reinforcement layers")
    bottom_layers: List[RebarLayer] = Field(default_factory=list, description="Bottom flexural reinforcement layers")
    stirrups: List[StirrupLayout] = Field(default_factory=list, description="Transverse shear stirrup zones")
