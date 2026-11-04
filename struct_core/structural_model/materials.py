"""
Material schemas: linear elastic, bilinear, and the reinforced-concrete materials (concrete, reinforcing bars).

All values are in the model's unit system (``StructuralModel.units``): moduli and strengths in its stress unit,
``unit_weight`` in its weight-density unit, ``rho`` in its mass-density unit. Concrete and rebar are linear elastic
materials for analysis (they subclass :class:`ElasticMaterial`) that also carry their design strengths.
"""

from typing import Annotated, Literal, Optional, Union
from pydantic import Field
from ..base import BaseSchemaModel, MaterialId


class BaseMaterial(BaseSchemaModel):
    """
    Base class for all material definitions.
    """
    id: MaterialId = Field(description="Unique material identifier")
    name: Optional[str] = Field(default=None, description="Human-readable material name (e.g. 'Steel A36')")
    unit_weight: Optional[float] = Field(default=None, ge=0.0, description="Weight density (force per unit volume, e.g. kN/m3, kip/in3, or pcf)")


class ElasticMaterial(BaseMaterial):
    """
    Isotropic linear elastic material definition.
    """
    type: Literal["elastic"] = "elastic"
    E: float = Field(gt=0.0, description="Young's modulus of elasticity")
    nu: float = Field(default=0.3, ge=-1.0, le=0.5, description="Poisson's ratio")
    rho: float = Field(default=0.0, ge=0.0, description="Mass density")


class ConcreteMaterial(ElasticMaterial):
    """
    Concrete: linear elastic for analysis, with its specified compressive strength for design.

    ``E`` is stored, not derived: struct_core holds data only, so the modulus (e.g. ACI 318 §19.2.2.1) is computed by
    whoever creates the material.
    """
    type: Literal["concrete"] = "concrete"
    fc: float = Field(gt=0.0, description="Specified compressive strength f'c (model stress unit)")
    nu: float = Field(default=0.2, ge=-1.0, le=0.5, description="Poisson's ratio")


class RebarMaterial(ElasticMaterial):
    """
    Reinforcing steel: linear elastic (``E`` = Es), with its specified yield and tensile strengths for design.
    """
    type: Literal["rebar"] = "rebar"
    fy: float = Field(gt=0.0, description="Specified yield strength fy (model stress unit)")
    fu: Optional[float] = Field(default=None, gt=0.0, description="Specified tensile strength fu (model stress unit)")


class BilinearMaterial(BaseMaterial):
    """
    Bilinear elastoplastic material definition.
    """
    type: Literal["bilinear"] = "bilinear"
    E: float = Field(gt=0.0, description="Initial elastic modulus")
    Et: float = Field(ge=0.0, description="Tangent modulus after yield")
    fy: float = Field(gt=0.0, description="Yield stress")
    nu: float = Field(default=0.3, ge=-1.0, le=0.5, description="Poisson's ratio")
    rho: float = Field(default=0.0, ge=0.0, description="Mass density")


# Discriminated union for polymorphic material deserialization
Material = Annotated[
    Union[ElasticMaterial, ConcreteMaterial, RebarMaterial, BilinearMaterial],
    Field(discriminator="type")
]
