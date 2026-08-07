"""
Bar schedule item and table aggregate schemas.
"""

from typing import List, Optional
from pydantic import Field
from ..base import BaseSchemaModel


class BarScheduleItem(BaseSchemaModel):
    """
    Single row entry in a rebar schedule / cut list table.
    """
    mark: str = Field(description="Bar mark identifier")
    bar_size: int = Field(gt=0, description="Bar size designation")
    quantity: int = Field(gt=0, description="Number of bars")
    cut_length: float = Field(gt=0.0, description="Individual bar cut length")
    total_length: float = Field(gt=0.0, description="Total length (quantity * cut_length)")
    weight: float = Field(gt=0.0, description="Total weight of this bar mark line item")
    shape_code: str = Field(default="STRAIGHT", description="ACI/CRSI standard bar shape code (e.g., 'STRAIGHT', '90_HOOK', 'STIRRUP')")
    location: Optional[str] = Field(default=None, description="Placement location description (e.g. 'Beam B1 Top')")


class BarSchedule(BaseSchemaModel):
    """
    Complete reinforcement schedule table for a member or project aggregate.
    """
    items: List[BarScheduleItem] = Field(default_factory=list, description="List of bar schedule line items")
    total_weight: float = Field(default=0.0, ge=0.0, description="Grand total reinforcement weight")
