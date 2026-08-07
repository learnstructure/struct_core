"""
Element-level design calculation schemas for beams, columns, slabs, and footings.
"""

from typing import List, Optional
from pydantic import Field
from ..base import BaseSchemaModel, ElementId
from .code_check import CodeCheckResult
from .material_design import FlexureDesignResult, ShearDesignResult


class ElementDesignResult(BaseSchemaModel):
    """
    Composite member design result containing strength checks, DCRs, and code clause compliance.
    """
    element_id: ElementId = Field(description="Target structural element ID")
    member_type: str = Field(default="beam", description="Member structural type ('beam', 'column', 'slab', 'footing', 'wall')")
    flexure: Optional[FlexureDesignResult] = Field(default=None, description="Flexural design summary")
    shear: Optional[ShearDesignResult] = Field(default=None, description="Shear design summary")
    code_checks: List[CodeCheckResult] = Field(default_factory=list, description="Detailed code checks performed")
    governing_dcr: float = Field(default=0.0, ge=0.0, description="Governing (maximum) DCR for element")
    passed: bool = Field(default=True, description="Overall element design pass status")
