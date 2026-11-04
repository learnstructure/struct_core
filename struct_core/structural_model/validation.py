"""
Validation logic for structural model referential integrity, duplicate IDs, and zero-length elements.
"""

import math
from typing import Dict, List, Set
from .model import StructuralModel
from .sections import GeneralSection


class StructuralValidationError(ValueError):
    """
    Exception raised when structural model validation rules are violated.
    """
    def __init__(self, errors: List[str]):
        self.errors = errors
        message = "Structural Model Validation Failed:\n" + "\n".join(f"  - {err}" for err in errors)
        super().__init__(message)


def validate_structural_model(model: StructuralModel, raise_error: bool = True) -> List[str]:
    """
    Validates essential structural model integrity:
    1. Unique IDs (nodes, elements, materials, sections, load cases).
    2. Referential integrity (elements -> nodes, sections; sections -> materials, with reinforcing-bar references
       naming rebar materials; supports -> nodes; loads -> nodes/elements).
    3. Zero-length element detection.

    Parameters
    ----------
    model : StructuralModel
        The structural model instance to validate.
    raise_error : bool, optional
        If True (default), raises StructuralValidationError if errors exist.
        If False, returns a list of error string messages.

    Returns
    -------
    List[str]
        List of validation error messages.
    """
    errors: List[str] = []

    # 1. Collect and check Node IDs
    node_map: Dict = {}
    node_ids: Set = set()
    for n in model.nodes:
        if n.id in node_ids:
            errors.append(f"Duplicate Node ID found: '{n.id}'")
        else:
            node_ids.add(n.id)
            node_map[n.id] = n

    # 2. Collect and check Material IDs
    material_types: Dict = {}
    for m in model.materials:
        if m.id in material_types:
            errors.append(f"Duplicate Material ID found: '{m.id}'")
        else:
            material_types[m.id] = m.type

    # 3. Collect and check Section IDs and their material references
    section_ids: Set = set()
    for s in model.sections:
        if s.id in section_ids:
            errors.append(f"Duplicate Section ID found: '{s.id}'")
        else:
            section_ids.add(s.id)
        if s.material_id not in material_types:
            errors.append(f"Section '{s.id}' references missing material_id '{s.material_id}'")
        for field in ("rebar_material_id", "transverse_rebar_material_id"):
            rebar_id = getattr(s, field, None)
            if rebar_id is None:
                continue
            if rebar_id not in material_types:
                errors.append(f"Section '{s.id}' references missing {field} '{rebar_id}'")
            elif material_types[rebar_id] != "rebar":
                errors.append(f"Section '{s.id}' {field} '{rebar_id}' is a '{material_types[rebar_id]}' material, "
                              f"not 'rebar'")
        cov = getattr(s, "cover", None)
        b = getattr(s, "b", None)
        h = getattr(s, "h", None)
        if cov is not None:
            if b is not None and cov >= b / 2.0:
                errors.append(f"Section '{s.id}' cover ({cov}) >= half width b/2 ({b/2.0})")
            if h is not None and cov >= h / 2.0:
                errors.append(f"Section '{s.id}' cover ({cov}) >= half depth h/2 ({h/2.0})")

    # 4. Check Elements & Element IDs
    element_ids: Set = set()
    element_map: Dict = {}
    for elem in model.elements:
        if elem.id in element_ids:
            errors.append(f"Duplicate Element ID found: '{elem.id}'")
        else:
            element_ids.add(elem.id)
            element_map[elem.id] = elem

        # Check Node References
        if elem.start_node not in node_ids:
            errors.append(f"Element '{elem.id}' references missing start_node '{elem.start_node}'")
        if elem.end_node not in node_ids:
            errors.append(f"Element '{elem.id}' references missing end_node '{elem.end_node}'")

        # Check the Section Reference of elements that have one (beam/truss); the section owns the material
        sec_id = getattr(elem, "section_id", None)
        if sec_id is not None and sec_id not in section_ids:
            errors.append(f"Element '{elem.id}' references missing section_id '{sec_id}'")
        elif sec_id is not None and getattr(elem, "type", "") == "beam":
            is_3d_model = getattr(model, "dimension", None) == "3D" or any(abs(n.z) > 1e-9 for n in model.nodes)
            if is_3d_model:
                sec_obj = next((s for s in model.sections if s.id == sec_id), None)
                if isinstance(sec_obj, GeneralSection):
                    if sec_obj.I2 is None or sec_obj.I2 <= 0.0:
                        errors.append(f"GeneralSection '{sec_id}' on beam element '{elem.id}' requires positive I2 for 3D analysis")
                    if sec_obj.J is None or sec_obj.J <= 0.0:
                        errors.append(f"GeneralSection '{sec_id}' on beam element '{elem.id}' requires positive J for 3D analysis")

        # Check Zero-Length Elements
        if elem.start_node in node_map and elem.end_node in node_map:
            n1 = node_map[elem.start_node]
            n2 = node_map[elem.end_node]
            dist = math.sqrt((n2.x - n1.x) ** 2 + (n2.y - n1.y) ** 2 + (n2.z - n1.z) ** 2)
            if dist < 1e-12:
                errors.append(f"Element '{elem.id}' has zero length between Node '{elem.start_node}' and Node '{elem.end_node}'")

    # 5. Check Supports
    if model.nodes and not model.supports:
        errors.append("Model contains nodes but has no supports (unconstrained mechanism)")

    seen_supports: Set = set()
    for sup in model.supports:
        if sup.node_id in seen_supports:
            errors.append(f"Duplicate support defined on Node '{sup.node_id}'")
        else:
            seen_supports.add(sup.node_id)
        if sup.node_id not in node_ids:
            errors.append(f"Support references missing node_id '{sup.node_id}'")

    # 6. Check Load Cases & Load References
    load_case_ids: Set = set()
    for lc in model.load_cases:
        if lc.id in load_case_ids:
            errors.append(f"Duplicate Load Case ID found: '{lc.id}'")
        else:
            load_case_ids.add(lc.id)

        for pload in lc.point_loads:
            if pload.node_id not in node_ids:
                errors.append(f"Point load in Load Case '{lc.id}' references missing node_id '{pload.node_id}'")

        for dload in lc.element_loads:
            if dload.element_id not in element_ids:
                errors.append(f"Distributed load in Load Case '{lc.id}' references missing element_id '{dload.element_id}'")
            if dload.start < 0.0 or dload.end > 1.0 or dload.start >= dload.end:
                errors.append(f"Distributed load in Load Case '{lc.id}' on element '{dload.element_id}' has invalid range [{dload.start}, {dload.end}]")

        for epload in getattr(lc, "element_point_loads", []):
            if epload.element_id not in element_ids:
                errors.append(f"Element point load in Load Case '{lc.id}' references missing element_id '{epload.element_id}'")
            if epload.position < 0.0 or epload.position > 1.0:
                errors.append(f"Element point load in Load Case '{lc.id}' on element '{epload.element_id}' has invalid position {epload.position}")

    # 7. Check Load Combinations
    for comb in model.load_combinations:
        for f in comb.factors:
            if f.load_case_id not in load_case_ids:
                errors.append(f"LoadCombination '{comb.id}' references missing load_case_id '{f.load_case_id}'")

    # 8. Check Mass Sources
    all_ms = list(model.mass_sources)
    if model.mass_source is not None and model.mass_source not in all_ms:
        all_ms.append(model.mass_source)
    for ms in all_ms:
        for f in ms.factors:
            if f.load_case_id not in load_case_ids:
                errors.append(f"MassSource '{ms.id}' references missing load_case_id '{f.load_case_id}'")

    # 9. Check Area Loads
    for al in model.area_loads:
        for nid in al.node_ids:
            if nid not in node_ids:
                errors.append(f"AreaLoad references missing node_id '{nid}'")

    if raise_error and errors:
        raise StructuralValidationError(errors)

    return errors
