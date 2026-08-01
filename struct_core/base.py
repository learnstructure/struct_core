"""
Base model configurations and ID type aliases for struct_core.
"""

from typing import Union
from pydantic import BaseModel, ConfigDict

# Common type aliases for object identification
IDType = Union[int, str]
NodeId = IDType
ElementId = IDType
MaterialId = IDType
SectionId = IDType
LoadCaseId = IDType
AnalysisCaseId = IDType


class BaseSchemaModel(BaseModel):
    """
    Base Pydantic model for all struct_core data structures.
    Enforces strict field validation and forbids unknown extra fields.
    """
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        validate_assignment=True,
    )
