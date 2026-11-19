"""
Named groups of structural objects (nodes, frame elements, and shell elements).

Groups preserve named object selections across CSI (SAP2000 / ETABS) exchange
and support group-based queries and design.
"""

from typing import List
from pydantic import Field, field_validator
from ..base import BaseSchemaModel, ElementId, NodeId


class ObjectGroup(BaseSchemaModel):
    """
    Named collection of nodes, frame/truss/spring elements, and shell elements.
    """
    id: str = Field(min_length=1, description="Unique group identifier")
    node_ids: List[NodeId] = Field(default_factory=list, description="Node IDs in this group")
    element_ids: List[ElementId] = Field(default_factory=list, description="Frame, truss, or spring element IDs in this group")
    shell_element_ids: List[ElementId] = Field(default_factory=list, description="Shell element IDs in this group")

    @field_validator("id")
    @classmethod
    def _check_id_not_blank(cls, val: str) -> str:
        if not val.strip():
            raise ValueError("ObjectGroup id must not be empty or whitespace")
        return val
