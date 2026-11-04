"""
Top-level DesignResult container for project-wide code design outputs.
"""

from typing import Any, Dict, List, Optional
from pydantic import Field, model_validator
from ..base import BaseSchemaModel, ElementId, ResultDict
from ..units import Units
from .code_check import CodeCheckResult
from .design_inputs import DesignInputs
from .element_design import ElementDesignResult


class DesignResult(BaseSchemaModel):
    """
    Top-level design result container wrapping element design results, governing DCRs, and code compliance.
    """
    design_code: str = Field(default="ACI 318-25", description="Design code standard identifier")
    units: Optional[Units] = Field(
        default=None, description="Units of every value in this result; None means the model units"
    )
    analysis_case_id: Optional[str] = Field(default=None, description="Analysis case or combination ID this design was evaluated from")
    model_fingerprint: Optional[str] = Field(default=None, description="Model input fingerprint hash at the time of design")
    element_results: Dict[ElementId, ElementDesignResult] = Field(default_factory=dict, description="Element design outputs keyed by ElementId")
    system_checks: List[CodeCheckResult] = Field(
        default_factory=list,
        description="Frame-level checks (slenderness, story drift, P-delta stability, beam-column joints)",
    )
    governing_dcr: float = Field(default=0.0, ge=0.0, description="Governing (maximum) DCR across all designed members")
    passed: bool = Field(default=False, description="Overall project design pass status flag")
    inputs: Optional[DesignInputs] = Field(
        default=None, description="Inputs the design was made with (materials, sections, foundation inputs, defaults)"
    )

    @model_validator(mode="after")
    def _verify_design_pass_and_dcr(self) -> "DesignResult":
        if self.element_results and not isinstance(self.element_results, ResultDict):
            object.__setattr__(self, "element_results", ResultDict(self.element_results))
        if self.element_results or self.system_checks:
            all_elem_pass = all(getattr(r, "passed", False) for r in self.element_results.values())
            all_sys_pass = all(getattr(c, "passed", False) for c in self.system_checks)
            dcrs = [float(getattr(r, "governing_dcr", 0.0) or 0.0) for r in self.element_results.values()] + [c.dcr for c in self.system_checks]
            gov_dcr = max(dcrs) if dcrs else 0.0
            object.__setattr__(self, "governing_dcr", gov_dcr)
            object.__setattr__(self, "passed", bool(all_elem_pass and all_sys_pass and gov_dcr <= 1.0))
        return self

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

