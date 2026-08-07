"""
Material strength design results (flexure, shear, axial, torsion).
"""

from typing import List, Optional
from pydantic import Field
from ..base import BaseSchemaModel


class FlexureDesignResult(BaseSchemaModel):
    """
    Flexural concrete/steel design calculation output.
    """
    required_steel_area: float = Field(ge=0.0, description="Required tension reinforcement area As (sq. in or sq. mm)")
    provided_steel_area: float = Field(ge=0.0, description="Provided tension reinforcement area As (sq. in or sq. mm)")
    phi_mn: float = Field(gt=0.0, description="Factored nominal flexural strength phi*Mn")
    mu: float = Field(ge=0.0, description="Factored design bending moment Mu")
    dcr: float = Field(ge=0.0, description="Demand/Capacity Ratio for flexure")
    neutral_axis_depth: float = Field(default=0.0, ge=0.0, description="Neutral axis depth c")
    steel_strain: float = Field(default=0.0, description="Net tensile strain in extreme tension steel epsilon_t")
    passed: bool = Field(description="Flexural strength adequacy status")
    messages: List[str] = Field(default_factory=list, description="Flexural design messages")


class ShearDesignResult(BaseSchemaModel):
    """
    Shear concrete/steel design calculation output.
    """
    required_shear_steel: float = Field(ge=0.0, description="Required transverse steel area per unit spacing Av/s")
    provided_shear_steel: float = Field(ge=0.0, description="Provided transverse steel area per unit spacing Av/s")
    phi_vc: float = Field(default=0.0, ge=0.0, description="Factored concrete shear strength phi*Vc")
    phi_vs: float = Field(default=0.0, ge=0.0, description="Factored steel shear strength phi*Vs")
    phi_vn: float = Field(gt=0.0, description="Total factored nominal shear strength phi*Vn")
    vu: float = Field(ge=0.0, description="Factored design shear force Vu")
    dcr: float = Field(ge=0.0, description="Demand/Capacity Ratio for shear")
    passed: bool = Field(description="Shear strength adequacy status")
    messages: List[str] = Field(default_factory=list, description="Shear design messages")


class MaterialDesignResult(BaseSchemaModel):
    """
    Composite material strength design summary.
    """
    flexure: Optional[FlexureDesignResult] = Field(default=None, description="Flexural design output")
    shear: Optional[ShearDesignResult] = Field(default=None, description="Shear design output")
