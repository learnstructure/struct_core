"""
Frame topology helpers shared by solvers' post-processing and design packages.

2D models lie in the x-y plane with y vertical; 3D models use z as the vertical axis.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Tuple

MemberRole = Literal["column", "beam", "brace"]


def vertical_axis(model: Any) -> str:
    """'z' for 3D models (or explicit vertical_axis='Z'), otherwise 'y'."""
    if hasattr(model, "vertical_axis") and model.vertical_axis:
        return str(model.vertical_axis).lower()
    if hasattr(model, "dimension") and model.dimension:
        if str(model.dimension).upper() == "2D":
            return "y"
        if str(model.dimension).upper() == "3D":
            return "z"
    inner = getattr(model, "model", None)
    if inner is not None:
        if hasattr(inner, "vertical_axis") and inner.vertical_axis:
            return str(inner.vertical_axis).lower()
        if hasattr(inner, "dimension") and inner.dimension:
            if str(inner.dimension).upper() == "2D":
                return "y"
            if str(inner.dimension).upper() == "3D":
                return "z"
    nodes = getattr(inner or model, "nodes", [])
    return "z" if any(abs(float(getattr(n, "z", 0.0) or 0.0)) > 1e-9 for n in nodes) else "y"


def _coords(node: Any, axis: str) -> Tuple[float, Tuple[float, ...]]:
    """(elevation, horizontal coordinates) of a node."""
    if axis == "z":
        return float(node.z), (float(node.x), float(node.y))
    return float(node.y), (float(node.x),)


def classify_frame_members(model: Any, tolerance: float = 0.01) -> Dict[Any, MemberRole]:
    """
    Classify frame (beam-type) elements by orientation.

    A member whose horizontal projection is below ``tolerance`` times its length is a column; one
    whose vertical projection is below ``tolerance`` times its length is a beam; anything else is a
    brace. Truss and spring elements are not classified.
    """
    axis = vertical_axis(model)
    nodes = {n.id: n for n in model.nodes}
    roles: Dict[Any, MemberRole] = {}
    for el in model.elements:
        if getattr(el, "type", "beam") != "beam":
            continue
        zi, hi = _coords(nodes[el.start_node], axis)
        zj, hj = _coords(nodes[el.end_node], axis)
        dv = abs(zj - zi)
        dh = math.dist(hi, hj)
        length = math.hypot(dv, dh)
        if length <= 0.0:
            continue
        if dh <= tolerance * length:
            roles[el.id] = "column"
        elif dv <= tolerance * length:
            roles[el.id] = "beam"
        else:
            roles[el.id] = "brace"
    return roles


@dataclass
class FrameStory:
    """One story of a frame: the columns spanning between two consecutive levels."""

    index: int
    bottom: float
    top: float
    column_ids: List[Any] = field(default_factory=list)

    @property
    def height(self) -> float:
        return self.top - self.bottom


def frame_levels(model: Any, tolerance: float = 1e-6) -> List[float]:
    """Sorted distinct elevations of column end nodes."""
    axis = vertical_axis(model)
    nodes = {n.id: n for n in model.nodes}
    roles = classify_frame_members(model)
    elevations: List[float] = []
    for el in model.elements:
        if roles.get(el.id) != "column":
            continue
        for nid in (el.start_node, el.end_node):
            z = _coords(nodes[nid], axis)[0]
            if not any(abs(z - e) <= tolerance for e in elevations):
                elevations.append(z)
    return sorted(elevations)


def frame_stories(model: Any, tolerance: float = 1e-6) -> List[FrameStory]:
    """
    Stories of a frame, bottom to top. Each column is assigned to the story between the
    levels at its ends; a column spanning several levels is assigned to its lowest story.
    """
    axis = vertical_axis(model)
    nodes = {n.id: n for n in model.nodes}
    roles = classify_frame_members(model)
    levels = frame_levels(model, tolerance)
    stories = [FrameStory(index=i, bottom=levels[i], top=levels[i + 1]) for i in range(len(levels) - 1)]
    for el in model.elements:
        if roles.get(el.id) != "column":
            continue
        z_low = min(_coords(nodes[el.start_node], axis)[0], _coords(nodes[el.end_node], axis)[0])
        for story in stories:
            if abs(story.bottom - z_low) <= tolerance:
                story.column_ids.append(el.id)
                break
    return [s for s in stories if s.column_ids]


def node_elevation(model: Any, node: Any) -> float:
    """Elevation of a node along the model's vertical axis."""
    return _coords(node, vertical_axis(model))[0]
