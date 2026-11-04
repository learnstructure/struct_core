"""
Element schemas representing structural members (Truss, Beam, Spring).

Truss and beam elements reference a section, which owns the material (``StructuralModel.material_of``).
"""

from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from pydantic import Field, model_validator
from ..base import BaseSchemaModel, ElementId, NodeId, SectionId


class BaseElement(BaseSchemaModel):
    """
    Base class for all structural finite elements.
    """
    id: ElementId = Field(description="Unique element identifier")
    start_node: NodeId = Field(description="Node ID at element start (i-node)")
    end_node: NodeId = Field(description="Node ID at element end (j-node)")
    name: Optional[str] = Field(default=None, description="Human-readable element name/tag")


class TrussElement(BaseElement):
    """
    2D/3D Truss element schema (axial forces only).
    """
    type: Literal["truss"] = "truss"
    section_id: SectionId = Field(description="Section (geometry and material) of the element")
    is_nonlinear: bool = Field(default=False, description="Flag for geometric/material nonlinearity")


class BeamElement(BaseElement):
    """
    2D/3D Frame beam-column element schema with optional end releases (hinges).
    """
    type: Literal["beam"] = "beam"
    section_id: SectionId = Field(description="Section (geometry and material) of the element")
    release_i: List[bool] = Field(
        default_factory=lambda: [False, False, False, False, False, False],
        description="End release flags at the i-node in member local axes: [u1 axial P, u2 shear V2, u3 shear V3, r1 torsion T, r2 moment M2, r3 moment M3]"
    )
    release_j: List[bool] = Field(
        default_factory=lambda: [False, False, False, False, False, False],
        description="End release flags at the j-node in member local axes: [u1 axial P, u2 shear V2, u3 shear V3, r1 torsion T, r2 moment M2, r3 moment M3]"
    )
    is_nonlinear: bool = Field(default=False, description="Flag for geometric/material nonlinearity")
    include_shear_deformation: bool = Field(
        default=False,
        description="Flag indicating whether shear deformation (Timoshenko beam theory) is considered"
    )
    roll_angle: float = Field(
        default=0.0,
        description="Member roll angle / rotation about longitudinal axis in degrees"
    )
    stiffness_modifiers: Optional[Dict[str, float]] = Field(
        default=None,
        description="Property / stiffness modifiers: A, As2, As3, J, I2, I3, mass, weight"
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_releases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in ("release_i", "release_j"):
                if key in data and data[key] is not None:
                    val = data[key]
                    if not isinstance(val, (list, tuple)) or len(val) not in (3, 6):
                        raise ValueError(f"{key} must have 3 (2D: u1, u2, r3) or 6 (u1, u2, u3, r1, r2, r3) entries")
                    if len(val) == 3:
                        data[key] = [bool(val[0]), bool(val[1]), False, False, False, bool(val[2])]
                    else:
                        data[key] = [bool(x) for x in val]
        return data

    @model_validator(mode="after")
    def _validate_stability(self) -> "BeamElement":
        rel_i = self.release_i
        rel_j = self.release_j
        if len(rel_i) != 6:
            raise ValueError("release_i must have 3 (2D: u1, u2, r3) or 6 (u1, u2, u3, r1, r2, r3) entries")
        if len(rel_j) != 6:
            raise ValueError("release_j must have 3 (2D: u1, u2, r3) or 6 (u1, u2, u3, r1, r2, r3) entries")

        if rel_i[0] and rel_j[0]:
            raise ValueError(f"BeamElement {self.id}: unstable mechanism - u1 (axial) released at both ends")
        if rel_i[1] and rel_j[1]:
            raise ValueError(f"BeamElement {self.id}: unstable mechanism - u2 (shear V2) released at both ends")
        if rel_i[2] and rel_j[2]:
            raise ValueError(f"BeamElement {self.id}: unstable mechanism - u3 (shear V3) released at both ends")
        if rel_i[3] and rel_j[3]:
            raise ValueError(f"BeamElement {self.id}: unstable mechanism - r1 (torsion T) released at both ends")
        if rel_i[4] and rel_j[4] and (rel_i[2] or rel_j[2]):
            raise ValueError(f"BeamElement {self.id}: unstable mechanism - r2 (moment M2) released at both ends and u3 (shear V3) released")
        if rel_i[5] and rel_j[5] and (rel_i[1] or rel_j[1]):
            raise ValueError(f"BeamElement {self.id}: unstable mechanism - r3 (moment M3) released at both ends and u2 (shear V2) released")
        return self


class SpringElement(BaseElement):
    """
    Spring element schema specifying directional stiffnesses.
    """
    type: Literal["spring"] = "spring"
    kx: float = Field(default=0.0, ge=0.0, description="Translational stiffness along x-axis")
    ky: float = Field(default=0.0, ge=0.0, description="Translational stiffness along y-axis")
    kz: float = Field(default=0.0, ge=0.0, description="Rotational/z-axis stiffness")


# Discriminated union for polymorphic element parsing
Element = Annotated[
    Union[TrussElement, BeamElement, SpringElement],
    Field(discriminator="type")
]


