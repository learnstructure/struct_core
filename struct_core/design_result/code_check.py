"""
Code check and demand-capacity ratio (DCR) schemas.
"""

from typing import List, Optional
from pydantic import Field
from ..base import BaseSchemaModel


class CodeCheckResult(BaseSchemaModel):
    """
    Evaluation result of a specific building code clause/provision check.
    """
    clause: str = Field(description="Governing code clause ID (e.g. 'ACI 318-19 §22.5.1')")
    description: Optional[str] = Field(default=None, description="Brief description of code check")
    demand: float = Field(description="Factored design demand (Mu, Vu, Pu, etc.)")
    capacity: float = Field(gt=0.0, description="Factored nominal design capacity (phi*Mn, phi*Vn, etc.)")
    dcr: float = Field(ge=0.0, description="Demand/Capacity Ratio (demand / capacity)")
    passed: bool = Field(description="Pass/Fail compliance status flag (dcr <= 1.0)")
    messages: List[str] = Field(default_factory=list, description="Diagnostic messages, warnings, or design notes")
