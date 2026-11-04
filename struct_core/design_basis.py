"""
Seismic design basis recorded on a Project by the load tools (ELF, response spectrum) and read
by analysis post-processing (story drift, stability) and code design (ACI 318 Chapter 18).
"""

from typing import Any, Dict, List, Optional
from pydantic import Field
from .base import BaseSchemaModel


class SeismicDesignBasis(BaseSchemaModel):
    """ASCE 7 seismic design parameters of the seismic-force-resisting system."""

    system: str = Field(description="Seismic force-resisting system key, e.g. 'rc_smf', 'rc_imf', 'rc_omf'")
    r_factor: float = Field(gt=0.0, description="Response modification coefficient R (ASCE 7 Table 12.2-1)")
    omega_0: float = Field(gt=0.0, description="Overstrength factor Omega_0 (Table 12.2-1)")
    cd: float = Field(gt=0.0, description="Deflection amplification factor Cd (Table 12.2-1)")
    importance_factor: float = Field(default=1.0, gt=0.0, description="Seismic importance factor Ie (Section 11.5.1)")
    risk_category: str = Field(default="II", description="Risk Category (Table 1.5-1)")
    sds: Optional[float] = Field(default=None, description="Design spectral acceleration SDS (g)")
    sd1: Optional[float] = Field(default=None, description="Design spectral acceleration SD1 (g)")
    s1: Optional[float] = Field(default=None, description="Mapped MCE_R spectral acceleration S1 (g)")
    seismic_design_category: Optional[str] = Field(default=None, description="Seismic Design Category (Section 11.6)")
    redundancy_factor: float = Field(default=1.0, gt=0.0, description="Redundancy factor rho (Section 12.3.4)")
    procedure: str = Field(description="Analysis procedure: 'elf' or 'rsa'")
    lateral_case_ids: List[str] = Field(
        default_factory=list, description="Load or analysis case IDs carrying the seismic lateral effect, one per direction"
    )
    directions: List[str] = Field(default_factory=list, description="Global directions of lateral_case_ids ('x' or 'y')")
    elf_inputs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Inputs of the ELF load generation (JSON values), so the weight-dependent story forces can be "
                    "regenerated when member sizes change; empty when they cannot be replayed",
    )
