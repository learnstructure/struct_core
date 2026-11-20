"""
Named story levels of a building model.

Stories represent levels above the structural base (``StructuralModel.base_elevation``),
preserving story names across CSI (ETABS / SAP2000) exchange, load generation, and drawings.
"""

import math
from pydantic import Field, field_validator
from ..base import BaseSchemaModel


class Story(BaseSchemaModel):
    """
    A named story level above the base datum.
    """

    name: str = Field(min_length=1, description="Story name (e.g. 'Story1', 'Roof')")
    elevation: float = Field(description="Story elevation in model length units (Z in 3D, Y in 2D)")

    @field_validator("name")
    @classmethod
    def _check_name_not_blank(cls, val: str) -> str:
        if not val.strip():
            raise ValueError("Story name must not be empty or whitespace")
        return val

    @field_validator("elevation")
    @classmethod
    def _check_elevation_finite(cls, val: float) -> float:
        fval = float(val)
        if not math.isfinite(fval):
            raise ValueError(f"Story elevation must be finite, got {val!r}")
        return fval
