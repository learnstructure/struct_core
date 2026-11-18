"""
Shell section and shell element schemas (slabs and walls).

A shell element is a 3- or 4-node area element (CSI "area object" with a shell section). Shell elements live in
``StructuralModel.shell_elements`` and their sections in ``StructuralModel.shell_sections``, apart from the two-node
frame elements and frame sections. They are not related to :class:`~struct_core.structural_model.loads.AreaLoad`,
which is a floor load distributed to frame members.

Local axes follow SAP2000 (CSI Analysis Reference Manual §10.6–10.7) and are computed only by
:func:`struct_core.geometry.shell_local_axes`. Lengths are in the model length unit.
"""

from typing import List, Literal, Optional, Tuple

from pydantic import Field, field_validator

from ..base import BaseSchemaModel, ElementId, MaterialId, NodeId, SectionId


class ShellSection(BaseSchemaModel):
    """
    Homogeneous shell section (CSI Analysis Reference Manual §10.1.1).

    - ``behavior``: ``"shell"`` (membrane and plate bending), ``"membrane"`` (in-plane only), or ``"plate"`` (bending
      only). CSI recommends the full shell unless the structure is planar and adequately restrained.
    - ``plate_theory``: ``"thick"`` (Mindlin/Reissner, with transverse shear deformation) or ``"thin"`` (Kirchhoff).
      CSI recommends the thick plate unless a thin-plate solution is to be matched.
    - ``thickness`` is the membrane thickness th (stiffness, self-weight, and mass); ``bending_thickness`` is the plate
      bending thickness thb (CSI), equal to ``thickness`` when not given.
    """
    type: Literal["shell"] = "shell"
    id: SectionId = Field(description="Unique section identifier (unique across frame and shell sections)")
    name: Optional[str] = Field(default=None, description="Human-readable section name (e.g. 'Slab 200')")
    material_id: MaterialId = Field(description="Material of the section")
    thickness: float = Field(gt=0.0, description="Membrane thickness th, model length unit")
    bending_thickness: Optional[float] = Field(
        default=None, gt=0.0, description="Plate bending thickness thb, model length unit (default: thickness)"
    )
    behavior: Literal["shell", "membrane", "plate"] = Field(
        default="shell", description="Full shell, membrane only, or plate bending only (CSI §10.1.1)"
    )
    plate_theory: Literal["thick", "thin"] = Field(
        default="thick", description="Thick (Mindlin/Reissner) or thin (Kirchhoff) plate bending (CSI §10.1.1)"
    )

    @property
    def effective_bending_thickness(self) -> float:
        """Plate bending thickness thb: ``bending_thickness`` if given, else ``thickness``."""
        return self.bending_thickness if self.bending_thickness is not None else self.thickness


class ShellElement(BaseSchemaModel):
    """
    3-node (triangle) or 4-node (quadrilateral) shell element.

    - ``node_ids``: corner nodes j1, j2, j3 (, j4) in order around the element. Local axis 3 points toward the viewer
      when j1-j2-j3 appears counterclockwise; a meshed floor should have every normal at +Z.
    - ``axis_angle``: CSI coordinate angle "ang" in degrees; rotates local axes 1 and 2 about +3 from the default
      orientation (or from the reference-vector orientation).
    - ``reference_vector``: optional global vector parallel to the local 3-2 plane, with a positive projection on
      local 2 (CSI §10.7.1, plane 32); replaces the default orientation.
    """
    type: Literal["shell"] = "shell"
    id: ElementId = Field(description="Unique element identifier (unique across frame and shell elements)")
    name: Optional[str] = Field(default=None, description="Human-readable element name")
    node_ids: List[NodeId] = Field(description="Corner nodes j1, j2, j3 (, j4) in order around the element")
    section_id: SectionId = Field(description="Shell section of the element")
    axis_angle: float = Field(default=0.0, description="CSI coordinate angle (degrees) of local axes 1-2 about +3")
    reference_vector: Optional[Tuple[float, float, float]] = Field(
        default=None, description="Global vector parallel to the local 3-2 plane (advanced local axes, CSI §10.7)"
    )

    @field_validator("node_ids")
    @classmethod
    def _check_nodes(cls, nodes: List[NodeId]) -> List[NodeId]:
        if len(nodes) not in (3, 4):
            raise ValueError(f"A shell element has 3 or 4 nodes, got {len(nodes)}")
        if len({str(n) for n in nodes}) != len(nodes):
            raise ValueError(f"Shell element nodes must be distinct, got {nodes}")
        return nodes

    @field_validator("reference_vector")
    @classmethod
    def _check_reference_vector(cls, vec: Optional[Tuple[float, float, float]]) -> Optional[Tuple[float, float, float]]:
        if vec is not None and all(abs(v) == 0.0 for v in vec):
            raise ValueError("reference_vector must not be zero")
        return vec
