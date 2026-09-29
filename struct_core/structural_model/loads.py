"""
Load schemas for point loads, distributed loads, ground motions, load cases, and load combinations.
"""

from typing import List, Optional
from pydantic import Field
from ..base import BaseSchemaModel, ElementId, LoadCaseId, NodeId


class PointLoad(BaseSchemaModel):
    """
    Concentrated force/moment applied to a node [Fx, Fy, Fz, Mx, My, Mz].
    """
    node_id: NodeId = Field(description="Target node ID")
    fx: float = Field(default=0.0, description="Force along X-axis")
    fy: float = Field(default=0.0, description="Force along Y-axis")
    fz: float = Field(default=0.0, description="Force along Z-axis")
    mx: float = Field(default=0.0, description="Moment about X-axis")
    my: float = Field(default=0.0, description="Moment about Y-axis")
    mz: float = Field(default=0.0, description="Moment about Z-axis")


class DistributedLoad(BaseSchemaModel):
    """
    Distributed load applied along an element.
    Supports uniform and linearly varying load profiles.
    """
    element_id: ElementId = Field(description="Target element ID")
    wx: float = Field(default=0.0, description="Uniform load intensity along X-axis")
    wy: float = Field(default=0.0, description="Uniform load intensity along Y-axis")
    wz: float = Field(default=0.0, description="Uniform load intensity along Z-axis")
    w1: Optional[float] = Field(default=None, description="Start load intensity at i-node (for linearly varying loads)")
    w2: Optional[float] = Field(default=None, description="End load intensity at j-node (for linearly varying loads)")
    is_local: bool = Field(default=False, description="Flag indicating local element coordinate system")


class AreaLoad(BaseSchemaModel):
    """
    Uniform surface pressure load applied over a floor area or panel.
    Can be attributed to bounding elements or floor levels via tributary area distribution.
    """
    id: Optional[str] = Field(default=None, description="Unique area load identifier")
    story_elevation: Optional[float] = Field(default=None, description="Floor level / elevation (Z or Y)")
    pressure: float = Field(default=0.0, description="Uniform surface pressure intensity (force / area, e.g. kN/m2 or psf)")
    load_type: str = Field(default="dead", description="Load nature/case: 'dead', 'live', 'snow', etc.")
    node_ids: List[NodeId] = Field(default_factory=list, description="Optional bounding polygon node IDs defining the loaded panel")
    tributary_width: Optional[float] = Field(default=None, description="Optional explicit tributary width for 2D frame projection")
    one_way: bool = Field(default=True, description="Whether one-way distribution or two-way distribution is assumed")
    span_direction_axis: str = Field(default="x", description="Direction axis of one-way slab span ('x' or 'y')")


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
    area_loads: List[AreaLoad] = Field(default_factory=list, description="List of area/surface loads assigned to this case")
    include_self_weight: bool = Field(default=False, description="Whether self-weight of elements should be automatically calculated")


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
AreaLoadSchema = AreaLoad
GroundMotionSchema = GroundMotion
LoadCaseSchema = LoadCase
LoadCaseFactorSchema = LoadCaseFactor
LoadCombinationSchema = LoadCombination
