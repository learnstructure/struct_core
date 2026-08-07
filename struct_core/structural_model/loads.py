"""
Load schemas for point loads, distributed loads, ground motions, load cases, and load combinations.
"""

from typing import List, Optional
from pydantic import Field
from ..base import BaseSchemaModel, ElementId, LoadCaseId, NodeId


class PointLoad(BaseSchemaModel):
    """
    Concentrated force/moment applied to a node [Fx, Fy, Mz].
    """
    node_id: NodeId = Field(description="Target node ID")
    fx: float = Field(default=0.0, description="Force along X-axis")
    fy: float = Field(default=0.0, description="Force along Y-axis")
    mz: float = Field(default=0.0, description="Moment about Z-axis")


class DistributedLoad(BaseSchemaModel):
    """
    Distributed load applied along an element.
    Supports uniform and linearly varying load profiles.
    """
    element_id: ElementId = Field(description="Target element ID")
    wx: float = Field(default=0.0, description="Uniform load intensity along X-axis")
    wy: float = Field(default=0.0, description="Uniform load intensity along Y-axis")
    w1: Optional[float] = Field(default=None, description="Start load intensity at i-node (for linearly varying loads)")
    w2: Optional[float] = Field(default=None, description="End load intensity at j-node (for linearly varying loads)")
    is_local: bool = Field(default=False, description="Flag indicating local element coordinate system")


class GroundMotion(BaseSchemaModel):
    """
    Ground motion acceleration time series record.
    """
    id: str = Field(description="Unique ground motion identifier")
    dt: float = Field(gt=0.0, description="Time step increment (seconds)")
    acc: List[float] = Field(description="Acceleration values time history series")
    name: Optional[str] = Field(default=None, description="Ground motion name (e.g. 'El Centro 1940')")


class LoadCase(BaseSchemaModel):
    """
    Logical grouping of applied point loads and element loads (e.g. 'Dead', 'Live', 'Wind').
    """
    id: LoadCaseId = Field(description="Unique load case identifier")
    name: Optional[str] = Field(default=None, description="Human-readable load case name")
    point_loads: List[PointLoad] = Field(default_factory=list, description="List of nodal point loads")
    element_loads: List[DistributedLoad] = Field(default_factory=list, description="List of distributed element loads")


class LoadCaseFactor(BaseSchemaModel):
    """
    Scale factor applied to a load case within a load combination.
    """
    load_case_id: LoadCaseId = Field(description="Referenced load case ID")
    factor: float = Field(default=1.0, description="Load factor scale multiplier")


class LoadCombination(BaseSchemaModel):
    """
    Factored linear combination of load cases (e.g. 1.2D + 1.6L).
    """
    id: str = Field(description="Unique load combination identifier")
    name: Optional[str] = Field(default=None, description="Human-readable load combination name")
    factors: List[LoadCaseFactor] = Field(default_factory=list, description="List of load cases with factors")


# Backward-compatible aliases
PointLoadSchema = PointLoad
DistributedLoadSchema = DistributedLoad
GroundMotionSchema = GroundMotion
LoadCaseSchema = LoadCase
LoadCaseFactorSchema = LoadCaseFactor
LoadCombinationSchema = LoadCombination
