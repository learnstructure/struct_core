"""
Validation logic for structural model referential integrity, duplicate IDs, and zero-length elements.
"""

import math
from typing import Dict, List, Set
from .model import StructuralModel


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
    2. Referential integrity (elements -> nodes, materials, sections; supports -> nodes; loads -> nodes/elements).
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
    material_ids: Set = set()
    for m in model.materials:
        if m.id in material_ids:
            errors.append(f"Duplicate Material ID found: '{m.id}'")
        else:
            material_ids.add(m.id)

    # 3. Collect and check Section IDs
    section_ids: Set = set()
    for s in model.sections:
        if s.id in section_ids:
            errors.append(f"Duplicate Section ID found: '{s.id}'")
        else:
            section_ids.add(s.id)

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

        # Check Material & Section References for elements that require them (beam/truss)
        mat_id = getattr(elem, "material_id", None)
        if mat_id is not None and mat_id not in material_ids:
            errors.append(f"Element '{elem.id}' references missing material_id '{mat_id}'")

        sec_id = getattr(elem, "section_id", None)
        if sec_id is not None and sec_id not in section_ids:
            errors.append(f"Element '{elem.id}' references missing section_id '{sec_id}'")

        # Check Zero-Length Elements
        if elem.start_node in node_map and elem.end_node in node_map:
            n1 = node_map[elem.start_node]
            n2 = node_map[elem.end_node]
            dist = math.sqrt((n2.x - n1.x) ** 2 + (n2.y - n1.y) ** 2 + (n2.z - n1.z) ** 2)
            if dist < 1e-12:
                errors.append(f"Element '{elem.id}' has zero length between Node '{elem.start_node}' and Node '{elem.end_node}'")

    # 5. Check Supports
    for sup in model.supports:
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

    if raise_error and errors:
        raise StructuralValidationError(errors)

    return errors
