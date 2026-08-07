"""
Time history result schemas for dynamic time series responses.
"""

from typing import Dict, List
from pydantic import Field
from ..base import BaseSchemaModel, NodeId
from .node_result import NodeDisplacement


class TimeStepResult(BaseSchemaModel):
    """
    State of the structure at a single time step t.
    """
    time: float = Field(ge=0.0, description="Time stamp in seconds")
    displacements: Dict[NodeId, NodeDisplacement] = Field(default_factory=dict, description="Nodal displacements at time t")


class TimeHistoryResult(BaseSchemaModel):
    """
    Dynamic time history integration response container.
    """
    dt: float = Field(gt=0.0, description="Time step increment (seconds)")
    time_steps: List[TimeStepResult] = Field(default_factory=list, description="Time history response series")
