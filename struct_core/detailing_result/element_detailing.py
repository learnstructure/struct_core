"""
Element-level reinforcement detailing result schemas.
"""

from typing import Optional
from pydantic import Field
from ..base import BaseSchemaModel, ElementId
from .anchorage import Anchorage
from .rebar import BarLayout
from .schedule import BarSchedule


class ElementDetailingResult(BaseSchemaModel):
    """
    Composite detailing output for a structural member (bar layout, bar schedule, anchorage).
    """
    element_id: ElementId = Field(description="Target structural element ID")
    member_type: str = Field(default="beam", description="Member structural type ('beam', 'column', 'slab', 'footing', 'wall')")
    bar_layout: BarLayout = Field(default_factory=BarLayout, description="Detailed 3D rebar arrangement")
    bar_schedule: BarSchedule = Field(default_factory=BarSchedule, description="Member bar schedule / cut list")
    anchorage: Optional[Anchorage] = Field(default=None, description="Anchorage and lap splice specification")
