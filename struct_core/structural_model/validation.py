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


def _shell_errors(model: StructuralModel, node_ids: Set, material_types: Dict, section_ids: Set,
                  element_ids: Set) -> List[str]:
    """Errors of the shell sections, shell elements, and shell loads. IDs must be unique across frame and shell
    sections, and across frame and shell elements. Shape errors follow CSI Analysis Reference Manual §10.2.1
    (``struct_core.geometry.check_model_shells``); its warnings are not errors and are left to the caller."""
    from ..geometry import check_model_shells

    errors: List[str] = []
    shell_section_ids: Set = set()
    for s in model.shell_sections:
        if s.id in shell_section_ids or s.id in section_ids:
            errors.append(f"Duplicate Section ID found: '{s.id}' (shell section)")
        shell_section_ids.add(s.id)
        if s.material_id not in material_types:
            errors.append(f"Shell section '{s.id}' references missing material_id '{s.material_id}'")

    shell_ids: Set = set()
    geometry_ok = True
    for el in model.shell_elements:
        if el.id in shell_ids or el.id in element_ids:
            errors.append(f"Duplicate Element ID found: '{el.id}' (shell element)")
        shell_ids.add(el.id)
        if el.section_id not in shell_section_ids:
            hint = " (a frame section; shell elements need a shell section)" if el.section_id in section_ids else ""
            errors.append(f"Shell element '{el.id}' references missing shell section '{el.section_id}'{hint}")
        missing = [nid for nid in el.node_ids if nid not in node_ids]
        if missing:
            geometry_ok = False
            errors.append(f"Shell element '{el.id}' references missing node(s) {missing}")

    if model.shell_elements and geometry_ok:
        try:
            issues = check_model_shells(model)
        except ValueError as exc:  # e.g. a reference_vector parallel to local axis 3
            errors.append(f"Shell element local axes: {exc}")
        else:
            errors.extend(i.message for i in issues if i.severity == "error")

    for lc in model.load_cases:
        for sl in lc.shell_loads:
            missing = [eid for eid in sl.element_ids if eid not in shell_ids]
            if missing:
                errors.append(f"Shell load in Load Case '{lc.id}' references missing shell element(s) {missing}")
    return errors


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

    # 10. Shell sections, shell elements, and shell loads
    errors.extend(_shell_errors(model, node_ids, material_types, section_ids, element_ids))

    # 11. Object groups
    shell_ids = {el.id for el in model.shell_elements}
    seen_groups: Set[str] = set()
    for group in model.groups:
        if group.name in seen_groups:
            errors.append(f"Duplicate group name found: '{group.name}'")
        else:
            seen_groups.add(group.name)
        missing_nodes = [nid for nid in group.node_ids if nid not in node_ids]
        if missing_nodes:
            errors.append(f"Group '{group.name}' references missing node(s) {missing_nodes}")
        missing_elems = [eid for eid in group.element_ids if eid not in element_ids]
        if missing_elems:
            errors.append(f"Group '{group.name}' references missing element(s) {missing_elems}")
        missing_shells = [sid for sid in group.shell_element_ids if sid not in shell_ids]
        if missing_shells:
            errors.append(f"Group '{group.name}' references missing shell element(s) {missing_shells}")

    if raise_error and errors:
        raise StructuralValidationError(errors)

    return errors
