"""
Anchorage, hook geometry, and lap splice detailing schemas.
"""

from typing import Optional
from pydantic import Field
from ..base import BaseSchemaModel


class HookGeometry(BaseSchemaModel):
    """
    Standard rebar hook dimensioning schema (90-deg, 135-deg, 180-deg standard/seismic hooks).
    """
    hook_type: str = Field(default="90", description="Hook type angle ('90', '135', '180')")
    tail_length: float = Field(gt=0.0, description="Straight extension tail length after bend")
    bend_radius: float = Field(gt=0.0, description="Inner bend radius")


class LapSplice(BaseSchemaModel):
    """
    Lap splice length and location specification.
    """
    splice_class: str = Field(default="Class A", description="Lap splice classification ('Class A', 'Class B')")
    splice_length: float = Field(gt=0.0, description="Required lap splice length")
    location: float = Field(ge=0.0, description="Distance along member to start of lap splice")


class Anchorage(BaseSchemaModel):
    """
    Development length and end anchorage specifications for reinforcing steel.
    """
    ld: float = Field(gt=0.0, description="Straight tension development length ld")
    hook: Optional[HookGeometry] = Field(default=None, description="End hook geometry if hooked anchorage used")
    splice: Optional[LapSplice] = Field(default=None, description="Lap splice details if spliced")
