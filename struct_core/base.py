"""
Base model configurations and ID type aliases for struct_core.
"""

from typing import Any, Union
from pydantic import BaseModel, ConfigDict


# Common type aliases for object identification
IDType = Union[int, str]
NodeId = IDType
ElementId = IDType
MaterialId = IDType
SectionId = IDType
LoadCaseId = IDType
AnalysisCaseId = IDType


class ResultDict(dict):
    """
    Dictionary mapping that allows seamless access via either int or str keys (e.g. 1 or '1').
    Ensures JSON-deserialized results (where keys are stringified) remain accessible with integer IDs.
    """
    def __getitem__(self, key: Any) -> Any:
        try:
            return super().__getitem__(key)
        except KeyError:
            if isinstance(key, int):
                return super().__getitem__(str(key))
            elif isinstance(key, str) and key.isdigit():
                try:
                    return super().__getitem__(int(key))
                except KeyError:
                    pass
            raise

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: Any) -> bool:
        if super().__contains__(key):
            return True
        if isinstance(key, int):
            return super().__contains__(str(key))
        elif isinstance(key, str) and key.isdigit():
            return super().__contains__(int(key))
        return False


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
