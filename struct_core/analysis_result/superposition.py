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

from typing import Dict, Iterable, List, Optional
from ..base import ElementId, NodeId
from .analysis_result import AnalysisResult
from .element_result import BeamSectionForce, ElementResult
from .node_result import NodeDisplacement, NodeReaction, NodeResult


def _combine_components(contributions: List[tuple], axial_indices: tuple = (0,)) -> List[float]:
    """Combine ``(factor, values, is_spectral)`` contributions component-wise.

    Signed contributions are summed linearly. For sign-less spectral cases:
    - For axial components (indices in ``axial_indices``, e.g. axial force P or vertical reaction):
      - If factor >= 0: adds magnitude in direction of signed sum (high compression branch).
      - If factor < 0: subtracts magnitude from signed sum (least compression / tension branch).
    - For flexural/shear/torsional components (indices not in ``axial_indices``):
      Seismic demand is cyclic and reversible. The governing maximum moment/shear is always
      combined constructively with gravity (|G| + |gamma_E * E|) to ensure full design capacity
      is checked on both high-axial and low-axial branches.
    """
    n = len(contributions[0][1])
    signed = [0.0] * n
    spectral_terms = []
    for fac, values, is_spectral in contributions:
        if is_spectral:
            spectral_terms.append((fac, values))
        else:
            for k in range(n):
                signed[k] += fac * float(values[k])

    if not spectral_terms:
        return signed

    result = list(signed)
    for k in range(n):
        s = signed[k]
        direction = 1.0 if s >= 0.0 else -1.0
        is_axial = k in axial_indices
        for fac, values in spectral_terms:
            val = abs(float(values[k]))
            if is_axial:
                fac_sign = 1.0 if fac >= 0.0 else -1.0
                result[k] += fac_sign * direction * (abs(fac) * val)
            else:
                fac_sign = 1.0 if s != 0.0 else (1.0 if fac >= 0.0 else -1.0)
                result[k] += fac_sign * direction * (abs(fac) * val)
    return result


def superpose_results(
    case_results: Dict[str, AnalysisResult],
    factors: Dict[str, float],
    output_case_id: str,
    spectral_case_ids: Iterable[str] = (),
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
    spectral_case_ids : Iterable[str]
        Cases holding sign-less peak responses (e.g. response spectrum results). Their factored
        magnitudes are added to each component with the sign of the signed (static) sum, so
        G +/- E yields the governing value |G| + |gamma_E * E|.

    Returns
    -------
    AnalysisResult
        Superposed AnalysisResult with combined nodal displacements, reactions,
        and element station forces.
    """
    # Active factors: ignore cases not in case_results or with zero factor
    spectral = set(spectral_case_ids)
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
        disp_terms = []
        reac_terms = []
        for cid, fac in active_factors.items():
            nr = case_results[cid].node_results.get(nid)
            if nr is None:
                continue
            is_spec = cid in spectral
            d = nr.displacement
            if d is not None:
                disp_terms.append((fac, (d.ux, d.uy, d.uz, d.rx, d.ry, d.rz), is_spec))
            r = nr.reaction
            if r is not None:
                reac_terms.append((fac, (r.fx, r.fy, r.fz, r.mx, r.my, r.mz), is_spec))

        ux, uy, uz, rx, ry, rz = _combine_components(disp_terms, axial_indices=(1, 2)) if disp_terms else [0.0] * 6
        node_disp = NodeDisplacement(ux=ux, uy=uy, uz=uz, rx=rx, ry=ry, rz=rz)
        node_reac = None
        if reac_terms:
            fx, fy, fz, mx, my, mz = _combine_components(reac_terms, axial_indices=(1, 2))
            node_reac = NodeReaction(fx=fx, fy=fy, fz=fz, mx=mx, my=my, mz=mz)
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
            # Check if this is a pure axial/truss element (shear and moment zero across all cases)
            has_flexure = any(
                abs(float(getattr(er, "max_moment", 0.0) or 0.0)) > 1e-9 or
                abs(float(getattr(er, "max_shear", 0.0) or 0.0)) > 1e-9
                for cid in active_factors
                if (er := case_results[cid].element_results.get(eid)) is not None
            )
            if has_flexure:
                raise ValueError(
                    f"Element '{eid}' has flexural/shear actions but lacks section station forces. "
                    "Linear superposition of bending moments and shear forces requires station forces "
                    "on ElementResult to prevent invalid envelope summation."
                )
            (p_tot,) = _combine_components([
                (fac, (float(getattr(er, "max_axial", 0.0) or 0.0),), cid in spectral)
                for cid, fac in active_factors.items()
                if (er := case_results[cid].element_results.get(eid)) is not None
            ])
            element_results[eid] = ElementResult(
                element_id=eid,
                forces=[],
                max_axial=p_tot,
                max_moment=0.0,
                max_shear=0.0,
            )
            continue

        n_stations = len(ref_er.forces)
        stations: List[BeamSectionForce] = []

        # Validate that all active cases have matching stations for this element
        for cid in active_factors:
            er = case_results[cid].element_results.get(eid)
            if er is None:
                raise ValueError(f"Cannot superpose: element '{eid}' missing in case '{cid}'")
            if len(er.forces) != n_stations:
                raise ValueError(
                    f"Cannot superpose: element '{eid}' station count mismatch "
                    f"({len(er.forces)} in case '{cid}' vs {n_stations} in reference case)"
                )
            for s_idx in range(n_stations):
                if abs(float(er.forces[s_idx].station) - float(ref_er.forces[s_idx].station)) > 1e-5:
                    raise ValueError(
                        f"Cannot superpose: element '{eid}' station location mismatch at index {s_idx} "
                        f"({er.forces[s_idx].station} in case '{cid}' vs {ref_er.forces[s_idx].station} in reference)"
                    )

        for s_idx in range(n_stations):
            station_loc = float(ref_er.forces[s_idx].station)
            terms = []
            for cid, fac in active_factors.items():
                er = case_results[cid].element_results.get(eid)
                sf = er.forces[s_idx]
                terms.append((fac, (sf.P, sf.Vy, sf.Vz, sf.T, sf.My, sf.Mz), cid in spectral))
            p, vy, vz, t, my, mz = _combine_components(terms, axial_indices=(0,))

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
        result_type="combination",
        carries_factored_actions=True,
        combination_factors={str(output_case_id): dict(active_factors)},
        node_results=node_results,
        element_results=element_results,
    )


def envelope_results(
    results: List[AnalysisResult],
    output_case_id: str = "Envelope",
) -> AnalysisResult:
    """
    Compile governing envelope across a set of AnalysisResult objects.

    Picks maximum absolute reactions, displacements, and element forces. Each element also keeps
    the station forces of every enveloped result in ``combination_forces`` (keyed by the result's
    ``analysis_case_id``, or by the keys of an already enveloped result), so the concurrent axial
    force and moments of each combination remain available to design.
    """
    valid_results = [r for r in results if r is not None]
    if not valid_results:
        return AnalysisResult(analysis_case_id=output_case_id)

    def _combination_forces(r: AnalysisResult, er: ElementResult) -> Dict[str, List[BeamSectionForce]]:
        if er.combination_forces:
            return dict(er.combination_forces)
        return {str(r.analysis_case_id): list(er.forces)} if er.forces else {}

    def _combination_reactions(r: AnalysisResult, nr: NodeResult) -> Dict[str, NodeReaction]:
        if nr.combination_reactions:
            return dict(nr.combination_reactions)
        return {str(r.analysis_case_id): nr.reaction} if nr.reaction is not None else {}

    if len(valid_results) == 1:
        res_copy = valid_results[0].model_copy(deep=True)
        res_copy.analysis_case_id = output_case_id
        for nr in res_copy.node_results.values():
            nr.combination_reactions = _combination_reactions(valid_results[0], nr)
        for er in res_copy.element_results.values():
            er.combination_forces = _combination_forces(valid_results[0], er)
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
        combination_reactions: Dict[str, NodeReaction] = {}

        for r in valid_results:
            nr = r.node_results.get(nid)
            if nr is None:
                continue
            combination_reactions.update(_combination_reactions(r, nr))
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
            combination_reactions=combination_reactions,
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

        combination_forces: Dict[str, List[BeamSectionForce]] = {}
        for r in valid_results:
            if eid in r.element_results:
                combination_forces.update(_combination_forces(r, r.element_results[eid]))

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
            combination_forces=combination_forces,
            max_axial=max_ax,
            max_moment=max_mo,
            max_shear=max_sh,
        )

    return AnalysisResult(
        analysis_case_id=output_case_id,
        result_type="envelope",
        carries_factored_actions=any(getattr(r, "carries_factored_actions", False) for r in valid_results),
        governing_combinations=[r.analysis_case_id for r in valid_results],
        combination_factors={k: dict(v) for r in valid_results for k, v in (r.combination_factors or {}).items()},
        node_results=node_results,
        element_results=element_results,
    )
