"""
The inputs a design was made with, recorded on its DesignResult so reports, drawings and audits can state them.
"""

from typing import List, Optional, Union
from pydantic import Field
from ..base import BaseSchemaModel
from ..structural_model.materials import Material
from ..structural_model.sections import Section


class AppliedDefault(BaseSchemaModel):
    """A default value a tool used because the user gave none, as defined (in its reference unit)."""
    name: str = Field(description="Input name, e.g. 'allowable_bearing_pressure', 'cover', 'fy'")
    value: Union[float, str] = Field(description="The default value, in its reference unit")
    unit: Optional[str] = Field(default=None, description="Reference unit of value (e.g. 'kPa', 'in'); None if unitless")
    source: str = Field(description="Where the default comes from, e.g. 'ACI 318-25 Table 20.5.1.3.1'")
    applies_to: Optional[str] = Field(default=None, description="ID of the section or material it was applied to")


class DesignInputs(BaseSchemaModel):
    """Inputs of a code design, in model units: the materials and sections designed, and the foundation inputs."""
    design_code: str = Field(description="Design code and edition, e.g. 'ACI 318-25'")
    materials: List[Material] = Field(
        default_factory=list, description="Materials of the designed sections, as used (concrete f'c, rebar fy, ...)"
    )
    sections: List[Section] = Field(
        default_factory=list, description="Designed sections, as used (geometry, material references, cover)"
    )
    allowable_bearing_pressure: Optional[float] = Field(
        default=None, gt=0.0,
        description="Allowable soil bearing pressure for footings under service loads (model pressure unit); "
                    "None when foundations were not designed",
    )
    footing_cover: Optional[float] = Field(
        default=None, gt=0.0, description="Clear cover of footing reinforcement (model length unit)"
    )
    defaults_applied: List[AppliedDefault] = Field(
        default_factory=list, description="Defaults used where the user gave no value"
    )
