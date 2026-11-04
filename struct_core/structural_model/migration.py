"""
Migration of models saved before sections owned their material (struct_core 0.2, 2026-10).

Those models stored ``material_id`` on each truss / beam element. Loading one moves the material onto the element's
section. A section whose elements used different materials is split: the material with the most elements keeps the
section ID, each other material gets a copy ``<section>_<material>`` and its elements are re-pointed.
"""

from typing import Any, Dict, List


def _get(item: Any, key: str) -> Any:
    return item.get(key) if isinstance(item, dict) else getattr(item, key, None)


def _with(item: Any, **update: Any) -> Any:
    return {**item, **update} if isinstance(item, dict) else item.model_copy(update=update)


def migrate_element_materials(data: Any) -> Any:
    """Return ``data`` (the raw input of a ``StructuralModel``) with element materials moved onto sections.

    Data without element ``material_id`` keys is returned unchanged.
    """
    if not isinstance(data, dict):
        return data
    raw_elements = data.get("elements") or []
    if not any(isinstance(e, dict) and "material_id" in e for e in raw_elements):
        return data

    elements: List[Any] = [dict(e) if isinstance(e, dict) else e for e in raw_elements]
    sections: List[Any] = list(data.get("sections") or [])
    position = {_get(s, "id"): i for i, s in enumerate(sections)}

    # section -> material -> positions of the elements that used it, in element order
    uses: Dict[Any, Dict[Any, List[int]]] = {}
    for i, element in enumerate(elements):
        if not isinstance(element, dict) or "material_id" not in element:
            continue
        material_id = element.pop("material_id")
        section_id = element.get("section_id")
        if material_id is not None and section_id is not None:
            uses.setdefault(section_id, {}).setdefault(material_id, []).append(i)

    taken = set(position)
    for section_id, by_material in uses.items():
        if section_id not in position:
            continue  # a missing section is reported by validate_structural_model
        index = position[section_id]
        ranked = sorted(by_material.items(), key=lambda item: (-len(item[1]), item[1][0]))
        kept = _get(sections[index], "material_id")
        if kept is None:
            kept = ranked[0][0]
            sections[index] = _with(sections[index], material_id=kept)
        for material_id, element_positions in ranked:
            if material_id == kept:
                continue
            new_id, n = f"{section_id}_{material_id}", 2
            while new_id in taken:
                new_id, n = f"{section_id}_{material_id}_{n}", n + 1
            taken.add(new_id)
            sections.append(_with(sections[index], id=new_id, material_id=material_id))
            for p in element_positions:
                elements[p]["section_id"] = new_id

    # A section no element used gets the model's material when there is only one; otherwise it stays without one
    # and validation names it.
    materials = data.get("materials") or []
    if len(materials) == 1:
        only = _get(materials[0], "id")
        sections = [s if _get(s, "material_id") is not None else _with(s, material_id=only) for s in sections]

    migrated = {**data, "elements": elements, "sections": sections}
    metadata = data.get("metadata")
    if isinstance(metadata, dict):  # the data is now in the current format; its old version stamp no longer applies
        migrated["metadata"] = {k: v for k, v in metadata.items() if k != "schema_version"}
    return migrated
