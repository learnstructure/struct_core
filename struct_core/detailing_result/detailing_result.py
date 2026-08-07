"""
Top-level DetailingResult container for project-wide reinforcement detailing outputs.
"""

from typing import Dict, Optional
from pydantic import Field
from ..base import BaseSchemaModel, ElementId
from .element_detailing import ElementDetailingResult
from .schedule import BarSchedule


class DetailingResult(BaseSchemaModel):
    """
    Top-level detailing result container holding member reinforcement layouts, bar schedules, and aggregate cut lists.
    """
    element_results: Dict[ElementId, ElementDetailingResult] = Field(default_factory=dict, description="Member detailing outputs keyed by ElementId")
    aggregate_schedule: Optional[BarSchedule] = Field(default=None, description="Project-wide aggregate reinforcement schedule")
