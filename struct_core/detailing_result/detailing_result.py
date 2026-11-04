"""
Top-level DetailingResult container for project-wide reinforcement detailing outputs.
"""

from typing import Dict, Literal, Optional
from pydantic import Field, model_validator
from ..base import BaseSchemaModel, ElementId, ResultDict
from ..units import Units
from .element_detailing import ElementDetailingResult
from .schedule import BarSchedule


class DetailingResult(BaseSchemaModel):
    """
    Top-level detailing result container holding member reinforcement layouts, bar schedules, and aggregate cut lists.
    """
    analysis_case_id: Optional[str] = Field(default=None, description="Analysis case or combination ID this detailing was produced from")
    model_fingerprint: Optional[str] = Field(default=None, description="Model input fingerprint hash at the time of detailing")
    units: Optional[Units] = Field(
        default=None, description="Units of every value in this result; None means the model units"
    )
    bar_system: Literal["US", "metric"] = Field(
        default="US",
        description="Reinforcement bar sizing system ('US' for # numbers, 'metric' for mm diameters)",
    )
    element_results: Dict[ElementId, ElementDetailingResult] = Field(default_factory=dict, description="Member detailing outputs keyed by ElementId")
    aggregate_schedule: Optional[BarSchedule] = Field(default=None, description="Project-wide aggregate reinforcement schedule")

    @model_validator(mode="after")
    def _wrap_result_dicts(self) -> "DetailingResult":
        if self.element_results and not isinstance(self.element_results, ResultDict):
            object.__setattr__(self, "element_results", ResultDict(self.element_results))
        return self
