"""
Top-level DesignResult container for project-wide code design outputs.
"""

from typing import Dict
from pydantic import Field
from ..base import BaseSchemaModel, ElementId
from .element_design import ElementDesignResult


class DesignResult(BaseSchemaModel):
    """
    Top-level design result container wrapping element design results, governing DCRs, and code compliance.
    """
    design_code: str = Field(default="ACI 318-19", description="Design code standard identifier")
    element_results: Dict[ElementId, ElementDesignResult] = Field(default_factory=dict, description="Element design outputs keyed by ElementId")
    governing_dcr: float = Field(default=0.0, ge=0.0, description="Governing (maximum) DCR across all designed members")
    passed: bool = Field(default=True, description="Overall project design pass status flag")

    @property
    def checks(self) -> list:
        """Return list of element design checks for UI tables and inspection."""
        items = []
        for eid, edr in self.element_results.items():
            pu_r = edr.flexure.dcr if edr.flexure and edr.member_type == "column" else None
            mu_r = edr.flexure.dcr if edr.flexure else None
            items.append(type("CheckItem", (), {
                "element_id": str(eid),
                "check_type": edr.member_type.upper(),
                "pu_ratio": pu_r,
                "mu_ratio": mu_r,
                "dcr": float(getattr(edr, "governing_dcr", 0.0) or 0.0),
                "governing_combo": "Envelope",
                "status": "PASS" if getattr(edr, "passed", False) else "FAIL",
            })())
        return items

