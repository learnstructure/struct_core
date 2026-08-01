"""
Material schemas for linear elastic and nonlinear materials.
"""

from typing import Annotated, Literal, Optional, Union
from pydantic import Field
from .base import BaseSchemaModel, MaterialId


class BaseMaterial(BaseSchemaModel):
    """
    Base class for all material definitions.
    """
    id: MaterialId = Field(description="Unique material identifier")
    name: Optional[str] = Field(default=None, description="Human-readable material name (e.g. 'Steel A36')")


class ElasticMaterial(BaseMaterial):
    """
    Isotropic linear elastic material definition.
    """
    type: Literal["elastic"] = "elastic"
    E: float = Field(gt=0.0, description="Young's modulus of elasticity")
    nu: float = Field(default=0.3, ge=-1.0, le=0.5, description="Poisson's ratio")
    rho: float = Field(default=0.0, ge=0.0, description="Mass density")


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
    Union[ElasticMaterial, BilinearMaterial],
    Field(discriminator="type")
]

# Backward-compatible aliases
BaseMaterialSchema = BaseMaterial
ElasticMaterialSchema = ElasticMaterial
BilinearMaterialSchema = BilinearMaterial
MaterialSchema = Material
