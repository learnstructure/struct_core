"""
Result schemas of shell elements: stress resultants per unit length at Gauss points, element corners, and nodes.

Names and signs follow the CSI Analysis Reference Manual (SAP2000 27), §10.18 "Internal Force and Stress Output", so
that results compare one to one with SAP2000 and ETABS:

- F11, F22: membrane direct forces; F12: membrane shear force (force per length).
- M11, M22: plate bending moments; M12: twisting moment (moment per length). M11 = -integral of x3 * sigma11 over
  the thickness, so a positive moment gives tension at the bottom (negative x3) face.
- V13, V23: transverse shear forces (force per length).

Values are in the element's local 1-2-3 axes (``struct_core.geometry.shell_local_axes``), except node-averaged values,
which are in the common axes stated with them.
"""

from typing import Any, Dict, List, Optional, Tuple

from pydantic import Field

from ..base import BaseSchemaModel, ElementId, NodeId


class ShellForces(BaseSchemaModel):
    """The eight stress resultants of a shell at one point, per unit length (CSI §10.18)."""
    F11: float = Field(default=0.0, description="Membrane direct force along local 1, per unit length")
    F22: float = Field(default=0.0, description="Membrane direct force along local 2, per unit length")
    F12: float = Field(default=0.0, description="Membrane shear force, per unit length")
    M11: float = Field(default=0.0, description="Bending moment M11 = -int(x3 sigma11), per unit length")
    M22: float = Field(default=0.0, description="Bending moment M22 = -int(x3 sigma22), per unit length")
    M12: float = Field(default=0.0, description="Twisting moment M12 = -int(x3 sigma12), per unit length")
    V13: float = Field(default=0.0, description="Transverse shear force on the 1-face, per unit length")
    V23: float = Field(default=0.0, description="Transverse shear force on the 2-face, per unit length")

    def as_list(self) -> List[float]:
        """Values in the order of ``struct_core.geometry.SHELL_FORCE_KEYS``."""
        return [self.F11, self.F22, self.F12, self.M11, self.M22, self.M12, self.V13, self.V23]


def shell_forces_from_array(values: Any) -> ShellForces:
    """A :class:`ShellForces` from eight values ordered as ``SHELL_FORCE_KEYS``."""
    v = [float(x) for x in values]
    if len(v) != 8:
        raise ValueError(f"A shell force record needs 8 values (F11 ... V23), got {len(v)}")
    return ShellForces(F11=v[0], F22=v[1], F12=v[2], M11=v[3], M22=v[4], M12=v[5], V13=v[6], V23=v[7])


class ShellElementResult(BaseSchemaModel):
    """
    Stress resultants of one shell element, in its local 1-2-3 axes.

    ``gauss_points`` holds the values at the 2 x 2 Gauss points of a quadrilateral (or the integration points of a
    triangle). ``corners`` holds the values extrapolated to the element's nodes, in the order of
    ``ShellElement.node_ids``, as SAP2000 reports them (table "Element Forces - Area Shells").

    For an envelope, ``gauss_points`` and ``corners`` hold the value of largest magnitude of each component over the
    enveloped results; these are not concurrent. The concurrent corner values of each enveloped result are in
    ``combination_corners``.
    """
    element_id: ElementId = Field(description="Shell element ID")
    gauss_points: List[ShellForces] = Field(default_factory=list, description="Resultants at the integration points")
    corners: List[ShellForces] = Field(default_factory=list, description="Resultants extrapolated to the element nodes")
    combination_corners: Dict[str, List[ShellForces]] = Field(
        default_factory=dict,
        description="Corner resultants of every enveloped combination, keyed by combination ID (set by "
                    "envelope_results)",
    )


class ShellNodeForces(BaseSchemaModel):
    """
    Resultants averaged at a node over the shell elements of one plane (``struct_core.geometry.
    average_shell_node_forces``). A node where a slab meets a wall has one record per plane.
    """
    node_id: NodeId = Field(description="Node ID")
    element_ids: List[ElementId] = Field(description="Elements averaged in this plane group")
    normal: Tuple[float, float, float] = Field(description="Common axis 3 of the group (global components)")
    axis_1: Tuple[float, float, float] = Field(description="Common axis 1 of the group (global components)")
    forces: ShellForces = Field(description="Averaged resultants in the common axes")
    flipped_element_ids: List[ElementId] = Field(
        default_factory=list, description="Elements of the group whose normal is opposite to the common normal"
    )


ShellNodeResults = Dict[NodeId, List[ShellNodeForces]]
