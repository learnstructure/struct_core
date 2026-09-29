"""
Linear superposition and envelope calculation for AnalysisResult schemas.

In linear elastic finite element analysis (K * u = F), the Principle of Superposition holds:
    u_comb = sum(gamma_i * u_i)
    R_comb = sum(gamma_i * R_i)
    F_comb = sum(gamma_i * F_i)

This enables:
1. Solving primary load cases independently (Dead, Live, Wind, etc.).
2. Evaluating any number of load combinations in O(N) time without re-solving K * u = F.
3. Enveloping governing forces, displacements, and reactions across combinations.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from ..base import ElementId, NodeId
from .analysis_result import AnalysisResult
from .element_result import BeamSectionForce, ElementResult
from .node_result import NodeDisplacement, NodeReaction, NodeResult


def superpose_results(
    case_results: Dict[str, AnalysisResult],
    factors: Dict[str, float],
    output_case_id: str,
) -> AnalysisResult:
    """
    Compute linear superposition of analysis results according to combination factors.

    Parameters
    ----------
    case_results : Dict[str, AnalysisResult]
        Dictionary of solved AnalysisResults keyed by load_case_id.
    factors : Dict[str, float]
        Load factors keyed by load_case_id (e.g. {"DEAD": 1.2, "LIVE": 1.6}).
    output_case_id : str
        Identifier for the combined result (e.g. "1.2D+1.6L").

    Returns
    -------
    AnalysisResult
        Superposed AnalysisResult with combined nodal displacements, reactions,
        and element station forces.
    """
    # Active factors: ignore cases not in case_results or with zero factor
    active_factors = {
        cid: float(fac) for cid, fac in factors.items()
        if cid in case_results and abs(fac) > 1e-12
    }

    if not active_factors:
        return AnalysisResult(analysis_case_id=output_case_id)

    # 1. Superpose Nodal Displacements and Reactions
    # Gather all node IDs present across results
    all_node_ids = set()
    for cid in active_factors:
        all_node_ids.update(case_results[cid].node_results.keys())

    node_results: Dict[NodeId, NodeResult] = {}
    for nid in all_node_ids:
        ux = uy = uz = rx = ry = rz = 0.0
        fx = fy = fz = mx = my = mz = 0.0
        has_reaction = False

        for cid, fac in active_factors.items():
            nr = case_results[cid].node_results.get(nid)
            if nr is None:
                continue
            disp = nr.displacement
            if disp is not None:
                ux += fac * float(disp.ux)
                uy += fac * float(disp.uy)
                uz += fac * float(disp.uz)
                rx += fac * float(disp.rx)
                ry += fac * float(disp.ry)
                rz += fac * float(disp.rz)

            reac = nr.reaction
            if reac is not None:
                has_reaction = True
                fx += fac * float(reac.fx)
                fy += fac * float(reac.fy)
                fz += fac * float(reac.fz)
                mx += fac * float(reac.mx)
                my += fac * float(reac.my)
                mz += fac * float(reac.mz)

        node_disp = NodeDisplacement(ux=ux, uy=uy, uz=uz, rx=rx, ry=ry, rz=rz)
        node_reac = NodeReaction(fx=fx, fy=fy, fz=fz, mx=mx, my=my, mz=mz) if has_reaction else None
        node_results[nid] = NodeResult(node_id=nid, displacement=node_disp, reaction=node_reac)

    # 2. Superpose Element Station Forces
    all_element_ids = set()
    for cid in active_factors:
        all_element_ids.update(case_results[cid].element_results.keys())

    element_results: Dict[ElementId, ElementResult] = {}
    for eid in all_element_ids:
        # Find reference station count and station values from the first result that has this element
        ref_er = None
        for cid in active_factors:
            er = case_results[cid].element_results.get(eid)
            if er and er.forces:
                ref_er = er
                break

        if ref_er is None or not ref_er.forces:
            # Fallback if no station forces are present
            p_tot = vy_tot = vz_tot = my_tot = mz_tot = 0.0
            for cid, fac in active_factors.items():
                er = case_results[cid].element_results.get(eid)
                if er:
                    p_tot += fac * float(getattr(er, "max_axial", 0.0) or 0.0)
                    vy_tot += fac * float(getattr(er, "max_shear", 0.0) or 0.0)
                    mz_tot += fac * float(getattr(er, "max_moment", 0.0) or 0.0)
            element_results[eid] = ElementResult(
                element_id=eid,
                forces=[],
                max_axial=p_tot,
                max_moment=mz_tot,
                max_shear=vy_tot,
            )
            continue

        n_stations = len(ref_er.forces)
        stations: List[BeamSectionForce] = []

        for s_idx in range(n_stations):
            station_loc = float(ref_er.forces[s_idx].station)
            p = vy = vz = t = my = mz = 0.0

            for cid, fac in active_factors.items():
                er = case_results[cid].element_results.get(eid)
                if er and len(er.forces) > s_idx:
                    sf = er.forces[s_idx]
                    p += fac * float(sf.P)
                    vy += fac * float(sf.Vy)
                    vz += fac * float(sf.Vz)
                    t += fac * float(sf.T)
                    my += fac * float(sf.My)
                    mz += fac * float(sf.Mz)

            stations.append(
                BeamSectionForce(
                    station=station_loc,
                    P=p,
                    Vy=vy,
                    Vz=vz,
                    T=t,
                    My=my,
                    Mz=mz,
                )
            )

        # Envelopes for this element
        max_ax = max(stations, key=lambda s: abs(s.P)).P if stations else 0.0
        max_sh = max(stations, key=lambda s: max(abs(s.Vy), abs(s.Vz)))
        gov_sh = max_sh.Vy if abs(max_sh.Vy) >= abs(max_sh.Vz) else max_sh.Vz
        max_mo = max(stations, key=lambda s: max(abs(s.My), abs(s.Mz)))
        gov_mo = max_mo.Mz if abs(max_mo.Mz) >= abs(max_mo.My) else max_mo.My

        element_results[eid] = ElementResult(
            element_id=eid,
            forces=stations,
            max_axial=max_ax,
            max_moment=gov_mo,
            max_shear=gov_sh,
        )

    return AnalysisResult(
        analysis_case_id=output_case_id,
        node_results=node_results,
        element_results=element_results,
    )


def envelope_results(
    results: List[AnalysisResult],
    output_case_id: str = "Envelope",
) -> AnalysisResult:
    """
    Compile governing envelope across a set of AnalysisResult objects.

    Picks maximum absolute reactions, displacements, and element forces.
    """
    valid_results = [r for r in results if r is not None]
    if not valid_results:
        return AnalysisResult(analysis_case_id=output_case_id)

    if len(valid_results) == 1:
        res_copy = valid_results[0].model_copy(deep=True)
        res_copy.analysis_case_id = output_case_id
        return res_copy

    # 1. Envelope Nodes: pick the result that has the maximum displacement resultant
    all_node_ids = set()
    for r in valid_results:
        all_node_ids.update(r.node_results.keys())

    node_results: Dict[NodeId, NodeResult] = {}
    for nid in all_node_ids:
        # Governing displacement: max translation norm
        best_disp = None
        best_disp_norm = -1.0
        best_reac = None
        best_reac_norm = -1.0

        for r in valid_results:
            nr = r.node_results.get(nid)
            if nr is None:
                continue
            if nr.displacement is not None:
                d = nr.displacement
                norm_d = (d.ux**2 + d.uy**2 + d.uz**2)**0.5
                if norm_d > best_disp_norm:
                    best_disp_norm = norm_d
                    best_disp = d
            if nr.reaction is not None:
                re = nr.reaction
                norm_r = (re.fx**2 + re.fy**2 + re.fz**2)**0.5
                if norm_r > best_reac_norm:
                    best_reac_norm = norm_r
                    best_reac = re

        node_results[nid] = NodeResult(
            node_id=nid,
            displacement=best_disp if best_disp is not None else NodeDisplacement(),
            reaction=best_reac,
        )

    # 2. Envelope Elements: pick governing moment station forces and max axial/shear
    all_element_ids = set()
    for r in valid_results:
        all_element_ids.update(r.element_results.keys())

    element_results: Dict[ElementId, ElementResult] = {}
    for eid in all_element_ids:
        all_er = [r.element_results[eid] for r in valid_results if eid in r.element_results]
        if not all_er:
            continue

        # Governing station profile is the one producing the maximum absolute moment
        gov_er = max(all_er, key=lambda er: abs(getattr(er, "max_moment", 0.0) or 0.0))

        # Max absolute values across all results
        max_ax_val = max(all_er, key=lambda er: abs(getattr(er, "max_axial", 0.0) or 0.0))
        max_ax = max_ax_val.max_axial

        max_sh_val = max(all_er, key=lambda er: abs(getattr(er, "max_shear", 0.0) or 0.0))
        max_sh = max_sh_val.max_shear

        max_mo = gov_er.max_moment

        element_results[eid] = ElementResult(
            element_id=eid,
            forces=gov_er.forces,
            max_axial=max_ax,
            max_moment=max_mo,
            max_shear=max_sh,
        )

    return AnalysisResult(
        analysis_case_id=output_case_id,
        node_results=node_results,
        element_results=element_results,
    )
