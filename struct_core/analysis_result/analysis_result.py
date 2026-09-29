"""
Top-level composite AnalysisResult schema holding nodal, element, modal, and dynamic time history outputs.
"""

from typing import Dict, Optional
from pydantic import Field
from ..base import AnalysisCaseId, BaseSchemaModel, ElementId, NodeId
from .element_result import ElementResult
from .modal_result import ModalResult
from .node_result import NodeResult
from .time_history_result import TimeHistoryResult


class AnalysisResult(BaseSchemaModel):
    """
    Top-level analysis result container associated with an analysis case.
    Stores nodal displacements/reactions, element forces, modal results, and time history responses.
    """
    analysis_case_id: AnalysisCaseId = Field(description="Associated analysis case identifier")
    node_results: Dict[NodeId, NodeResult] = Field(default_factory=dict, description="Nodal output results keyed by NodeId")
    element_results: Dict[ElementId, ElementResult] = Field(default_factory=dict, description="Element output results keyed by ElementId")
    modal_result: Optional[ModalResult] = Field(default=None, description="Modal eigenvalue analysis results (if applicable)")
    time_history_result: Optional[TimeHistoryResult] = Field(default=None, description="Dynamic time history analysis results (if applicable)")

    @property
    def nodal_displacements(self) -> list:
        """Return list of nodal displacement summary objects with ux, uy, uz, rx, ry, rz."""
        items = []
        for nid, nr in self.node_results.items():
            d = getattr(nr, "displacement", None)
            if d is not None:
                item = type("DisplacementItem", (), {
                    "node_id": str(nid),
                    "ux": float(d.ux),
                    "uy": float(d.uy),
                    "uz": float(d.uz),
                    "rx": float(d.rx),
                    "ry": float(d.ry),
                    "rz": float(d.rz),
                })()
                items.append(item)
        return items

    @property
    def node_reactions(self) -> list:
        """Return list of nodal reaction summary objects with fx, fy, fz, mx, my, mz, Rx, Ry, Rz, Mx, My, Mz."""
        items = []
        for nid, nr in self.node_results.items():
            r = getattr(nr, "reaction", None)
            if r is not None:
                fx = float(getattr(r, "fx", 0.0) or 0.0)
                fy = float(getattr(r, "fy", 0.0) or 0.0)
                fz = float(getattr(r, "fz", 0.0) or 0.0)
                mx = float(getattr(r, "mx", 0.0) or 0.0)
                my = float(getattr(r, "my", 0.0) or 0.0)
                mz = float(getattr(r, "mz", 0.0) or 0.0)
                r_mag = (fx**2 + fy**2 + fz**2) ** 0.5
                m_mag = (mx**2 + my**2 + mz**2) ** 0.5
                item = type("ReactionItem", (), {
                    "node_id": str(nid),
                    "fx": fx, "fy": fy, "fz": fz,
                    "mx": mx, "my": my, "mz": mz,
                    "Rx": fx, "Ry": fy, "Rz": fz,
                    "Mx": mx, "My": my, "Mz": mz,
                    "R_resultant": r_mag,
                    "M_resultant": m_mag,
                })()
                items.append(item)
        return items

    @property
    def element_forces(self) -> list:
        """Return list of element section force summary objects for all member stations."""
        items = []
        for eid, er in self.element_results.items():
            forces = getattr(er, "forces", [])
            if forces:
                for f in forces:
                    p_val = float(getattr(f, "P", 0.0) or getattr(f, "axial", 0.0) or 0.0)
                    vy_val = float(getattr(f, "Vy", 0.0) or getattr(f, "V2", 0.0) or getattr(f, "shear", 0.0) or 0.0)
                    vz_val = float(getattr(f, "Vz", 0.0) or getattr(f, "V3", 0.0) or 0.0)
                    my_val = float(getattr(f, "My", 0.0) or getattr(f, "M2", 0.0) or 0.0)
                    mz_val = float(getattr(f, "Mz", 0.0) or getattr(f, "M3", 0.0) or getattr(f, "moment", 0.0) or 0.0)
                    m_gov = mz_val if abs(mz_val) >= abs(my_val) else my_val
                    v_gov = vy_val if abs(vy_val) >= abs(vz_val) else vz_val
                    t_val = float(getattr(f, "T", 0.0) or 0.0)

                    item = type("SectionForceItem", (), {
                        "element_id": str(eid),
                        "station": float(getattr(f, "station", 0.0)),
                        "P": p_val, "p": p_val,
                        "V2": vy_val, "v2": vy_val, "Vy": vy_val,
                        "V3": vz_val, "v3": vz_val, "Vz": vz_val,
                        "V": v_gov, "v": v_gov,
                        "T": t_val, "t": t_val,
                        "M2": my_val, "m2": my_val, "My": my_val,
                        "M3": mz_val, "m3": mz_val, "Mz": mz_val,
                        "M": m_gov, "m": m_gov,
                    })()
                    items.append(item)
            else:
                p_val = float(getattr(er, "max_axial", 0.0) or 0.0)
                v_val = float(getattr(er, "max_shear", 0.0) or 0.0)
                m_val = float(getattr(er, "max_moment", 0.0) or 0.0)
                item = type("SectionForceItem", (), {
                    "element_id": str(eid),
                    "station": 0.0,
                    "P": p_val, "p": p_val,
                    "V2": v_val, "v2": v_val, "Vy": v_val,
                    "V3": 0.0, "v3": 0.0, "Vz": 0.0,
                    "V": v_val, "v": v_val,
                    "T": 0.0, "t": 0.0,
                    "M2": 0.0, "m2": 0.0, "My": 0.0,
                    "M3": m_val, "m3": m_val, "Mz": m_val,
                    "M": m_val, "m": m_val,
                })()
                items.append(item)
        return items

