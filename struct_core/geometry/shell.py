"""
Geometry of shell elements: local axes, shape checks, corner weights, and the rotation and nodal averaging of
stress resultants.

This module is the single place where the local axes of a shell element are computed. Solvers, exchange with
SAP2000 and ETABS, drawing, and design call :func:`shell_local_axes` and never recompute the axes.

Local axes (CSI Analysis Reference Manual, SAP2000 27, §10.6 and §10.7):

- Axis 3 is normal to the element, toward the viewer when the path j1-j2-j3 appears counterclockwise. For a
  quadrilateral, the plane is spanned by the vectors that join the midpoints of the two pairs of opposite sides.
- By default the 3-2 plane is vertical and axis 2 points up (+Z). An element is horizontal when the sine of the angle
  between axis 3 and Z is below ``SHELL_HORIZONTAL_SINE`` (1e-3); axis 2 is then along +Y. Axis 1 completes the
  right-handed triad (e1 = e2 x e3).
- ``reference_vector`` (CSI "advanced local axes", plane 3-2): axis 2 is the component of the vector normal to axis 3.
  The vector must not be parallel to axis 3. CSI's option of a reference vector in the 3-1 plane is not provided.
- ``axis_angle`` (CSI "ang", degrees) then rotates axes 1 and 2 about +3, counterclockwise when +3 points toward the
  viewer.

All functions work on N elements at once. Element coordinates are an array of shape (N, k, 3), with k = 3 for
triangles and k = 4 for quadrilaterals, in the order of the element's nodes. Axes are returned as an (N, 3, 3) array
whose rows are e1, e2, e3 in global components, so that ``axes @ v_global`` gives local components (the convention of
the frame rotation matrix R in fem3d).

Stress resultants are ordered as ``SHELL_FORCE_KEYS``: F11, F22, F12, M11, M22, M12, V13, V23 (CSI §10.18), all per
unit length. M11 = -integral of x3 * sigma11 through the thickness, so a positive moment gives tension at the bottom
(negative x3) face.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

import numpy as np

# The ordering of the eight stress resultants of a shell (CSI Analysis Reference Manual §10.18)
SHELL_FORCE_KEYS: Tuple[str, ...] = ("F11", "F22", "F12", "M11", "M22", "M12", "V13", "V23")

# Sine of the angle between axis 3 and global Z below which an element is horizontal (CSI §10.6.2)
SHELL_HORIZONTAL_SINE = 1e-3

# Shape limits of CSI §10.2.1 "Shape Guidelines"
SHELL_WARP_WARN_DEG = 30.0      # largest angle between corner normals: best results below this
SHELL_WARP_LIMIT_DEG = 45.0     # ... and it should not exceed this
SHELL_ANGLE_LIMIT_DEG = 180.0   # inside angle at each corner must be less than this
SHELL_QUAD_ANGLE_RANGE_DEG = (45.0, 135.0)  # quadrilateral corners: best results within this range
SHELL_ASPECT_WARN = 4.0         # aspect ratio: best results below this
SHELL_ASPECT_LIMIT = 10.0       # ... and it should not exceed this

# Largest angle between the normals of two elements that are treated as lying in one plane, when results are
# averaged at a node and when normals are compared across a shared edge. Facets of a curved shell (a few degrees
# apart) are one plane; a slab meeting a wall (90 degrees) or a fold of a folded plate are not.
SHELL_PLANE_TOLERANCE_DEG = 15.0

_CLAUSE = "CSI Analysis Reference Manual §10.2.1"


def _as_coords(coords: Any) -> np.ndarray:
    x = np.asarray(coords, dtype=float)
    if x.ndim == 2:
        raise ValueError("Shell coordinates must have shape (N, k, 3); for one element, pass coords[None]")
    if x.ndim != 3 or x.shape[1] not in (3, 4) or x.shape[2] != 3:
        raise ValueError(f"Shell coordinates must have shape (N, 3, 3) or (N, 4, 3), got {x.shape}")
    if not np.all(np.isfinite(x)):
        raise ValueError("Shell coordinates contain non-finite values")
    return x


def _vector_area(x: np.ndarray) -> np.ndarray:
    """Vector area of each element (N, 3): normal to the element plane with the length of the projected area.

    For a quadrilateral it is half the cross product of the diagonals, which equals the cross product of the vectors
    joining the midpoints of opposite sides (CSI §10.6.1) and the area of the projection on that plane.
    """
    if x.shape[1] == 3:
        return 0.5 * np.cross(x[:, 1] - x[:, 0], x[:, 2] - x[:, 0])
    return 0.5 * np.cross(x[:, 2] - x[:, 0], x[:, 3] - x[:, 1])


def _unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _broadcast(value: Any, n: int, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.ndim == 0:
        return np.full(n, float(arr))
    if arr.shape != (n,):
        raise ValueError(f"{name} must be a scalar or have shape ({n},), got {arr.shape}")
    return arr


def shell_normals(coords: Any) -> np.ndarray:
    """Unit normal (local axis 3) of each element, shape (N, 3). Refuses elements of zero area."""
    x = _as_coords(coords)
    area_vec = _vector_area(x)
    area = np.linalg.norm(area_vec, axis=1)
    size = np.max(np.linalg.norm(x - np.roll(x, 1, axis=1), axis=2), axis=1)
    bad = np.nonzero(area <= 1e-12 * np.maximum(size, 1e-300) ** 2)[0]
    if bad.size:
        raise ValueError(f"Shell element(s) at index {bad.tolist()} have zero area (coincident or collinear nodes)")
    return area_vec / area[:, None]


def shell_areas(coords: Any) -> np.ndarray:
    """Area of each element projected on its plane (CSI §10.6.1), shape (N,)."""
    return np.linalg.norm(_vector_area(_as_coords(coords)), axis=1)


def shell_local_axes(
    coords: Any,
    axis_angle: Any = 0.0,
    reference_vector: Optional[Any] = None,
) -> np.ndarray:
    """
    Local axes 1-2-3 of N shell elements, following SAP2000 (CSI Analysis Reference Manual §10.6–10.7).

    Parameters
    ----------
    coords : array_like, shape (N, 3, 3) or (N, 4, 3)
        Global coordinates of the element nodes, in element node order.
    axis_angle : float or array_like (N,)
        CSI coordinate angle "ang" in degrees: rotation of axes 1 and 2 about +3 from the default (or
        reference-vector) orientation, counterclockwise when +3 points toward the viewer.
    reference_vector : array_like (3,) or (N, 3), optional
        Vector parallel to the local 3-2 plane, with a positive projection on local 2 (CSI §10.7.1, plane 32). A row
        of NaN keeps the default orientation for that element. The vector must not be parallel to axis 3.

    Returns
    -------
    numpy.ndarray, shape (N, 3, 3)
        Rows e1, e2, e3 of each element in global components.
    """
    x = _as_coords(coords)
    n = x.shape[0]
    e3 = shell_normals(x)

    # Default orientation (CSI §10.6.2): the 3-2 plane is vertical, axis 2 up; horizontal elements take +Y
    horizontal = np.hypot(e3[:, 0], e3[:, 1]) < SHELL_HORIZONTAL_SINE
    ref = np.where(horizontal[:, None], np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0]))

    if reference_vector is not None:
        rv = np.array(np.broadcast_to(np.asarray(reference_vector, dtype=float), (n, 3)))
        given = np.all(np.isfinite(rv), axis=1)
        if np.any(given):
            rv_len = np.linalg.norm(rv, axis=1)
            zero = given & (rv_len <= 0.0)
            if np.any(zero):
                raise ValueError(f"reference_vector is zero for element index {np.nonzero(zero)[0].tolist()}")
            sine = np.zeros(n)
            sine[given] = np.linalg.norm(np.cross(rv[given], e3[given]), axis=1) / rv_len[given]
            parallel = given & (sine < SHELL_HORIZONTAL_SINE)
            if np.any(parallel):
                raise ValueError(
                    f"reference_vector is parallel to local axis 3 for element index "
                    f"{np.nonzero(parallel)[0].tolist()} (CSI Analysis Reference Manual §10.7.1)"
                )
            ref[given] = rv[given]

    e2 = _unit(ref - np.sum(ref * e3, axis=1, keepdims=True) * e3)
    e1 = np.cross(e2, e3)

    ang = np.radians(_broadcast(axis_angle, n, "axis_angle"))
    c, s = np.cos(ang)[:, None], np.sin(ang)[:, None]
    e1r = c * e1 + s * e2
    e2r = -s * e1 + c * e2
    return np.stack([e1r, e2r, e3], axis=1)


def shell_corner_weights(coords: Any) -> np.ndarray:
    """
    Fraction of an element's area (and so of its mass or uniform load) lumped at each corner, shape (N, k).

    The fractions are proportional to the diagonal terms of the consistent mass matrix of the bilinear (quadrilateral)
    or linear (triangle) interpolation, as SAP2000 lumps shell mass (CSI Analysis Reference Manual §10.11). They are
    equal for triangles and parallelograms. Quadrilaterals are integrated with 2 x 2 Gauss points, which is exact here.
    """
    x = _as_coords(coords)
    n, k = x.shape[:2]
    if k == 3:
        shell_normals(x)  # refuse zero area
        return np.full((n, 3), 1.0 / 3.0)
    g = 1.0 / math.sqrt(3.0)
    diag = np.zeros((n, 4))
    xi_n = np.array([-1.0, 1.0, 1.0, -1.0])
    eta_n = np.array([-1.0, -1.0, 1.0, 1.0])
    for xi in (-g, g):
        for eta in (-g, g):
            shape = 0.25 * (1 + xi_n * xi) * (1 + eta_n * eta)
            d_xi = 0.25 * xi_n * (1 + eta_n * eta)
            d_eta = 0.25 * eta_n * (1 + xi_n * xi)
            x_xi = np.einsum("a,nai->ni", d_xi, x)
            x_eta = np.einsum("a,nai->ni", d_eta, x)
            jac = np.linalg.norm(np.cross(x_xi, x_eta), axis=1)
            diag += (shape ** 2)[None, :] * jac[:, None]
    total = diag.sum(axis=1, keepdims=True)
    if np.any(total <= 0.0):
        raise ValueError("Shell element of zero area")
    return diag / total


@dataclass(frozen=True)
class ShellShapeIssue:
    """A shape or orientation finding for one shell element (``severity`` 'error' refuses the element)."""
    element_id: Any
    check: Literal["zero_area", "warping", "inside_angle", "aspect_ratio", "flipped_normal", "normal_direction"]
    severity: Literal["warning", "error"]
    value: float
    limit: float
    message: str


def shell_shape_measures(coords: Any) -> Dict[str, np.ndarray]:
    """
    Shape measures of CSI Analysis Reference Manual §10.2.1 for N elements.

    Returns a dict with:
    - ``warping`` (N,): largest angle in degrees between the normals at any two corners (0 for triangles). The normal
      at a corner is perpendicular to the two sides that meet there; its sense is ignored (angle between the corner
      planes, 0° to 90°).
    - ``inside_angles`` (N, k): inside angle at each corner in degrees, measured in the element plane; 180 or more
      means a re-entrant corner.
    - ``aspect_ratio`` (N,): triangle, longest to shortest side; quadrilateral, the longer to the shorter distance
      between the midpoints of opposite sides.
    """
    x = _as_coords(coords)
    k = x.shape[1]
    e3 = _unit(_vector_area(x))
    nxt = np.roll(x, -1, axis=1) - x
    prv = np.roll(x, 1, axis=1) - x

    cross = np.cross(nxt, prv)
    sin_part = np.einsum("nki,ni->nk", cross, e3)
    cos_part = np.einsum("nki,nki->nk", nxt, prv)
    inside = np.degrees(np.arctan2(sin_part, cos_part)) % 360.0

    if k == 4:
        corner_n = cross / np.maximum(np.linalg.norm(cross, axis=2, keepdims=True), 1e-300)
        # Angle between the planes of two corners. The sense of a corner normal is ignored: it reverses at a
        # re-entrant corner of a flat element, which the inside-angle check reports.
        dots = np.abs(np.einsum("nai,nbi->nab", corner_n, corner_n))
        warping = np.degrees(np.arccos(np.clip(dots, 0.0, 1.0))).max(axis=(1, 2))
        mid = 0.5 * (x + np.roll(x, -1, axis=1))  # midpoints of sides 12, 23, 34, 41
        d1 = np.linalg.norm(mid[:, 1] - mid[:, 3], axis=1)
        d2 = np.linalg.norm(mid[:, 2] - mid[:, 0], axis=1)
        aspect = np.maximum(d1, d2) / np.maximum(np.minimum(d1, d2), 1e-300)
    else:
        warping = np.zeros(x.shape[0])
        sides = np.linalg.norm(nxt, axis=2)
        aspect = sides.max(axis=1) / np.maximum(sides.min(axis=1), 1e-300)
    return {"warping": warping, "inside_angles": inside, "aspect_ratio": aspect}


def check_shell_shapes(coords: Any, element_ids: Optional[Sequence[Any]] = None) -> List[ShellShapeIssue]:
    """
    Check N elements against the shape guidelines of CSI Analysis Reference Manual §10.2.1.

    - Zero area: error.
    - Inside angle at a corner: error at 180° or more; for quadrilaterals, a warning outside 45°–135°.
    - Aspect ratio: warning above 4, error above 10.
    - Warping of quadrilaterals (largest angle between corner normals): warning above 30°, error above 45°.
    """
    x = _as_coords(coords)
    ids = list(element_ids) if element_ids is not None else list(range(x.shape[0]))
    if len(ids) != x.shape[0]:
        raise ValueError("element_ids must have one entry per element")
    issues: List[ShellShapeIssue] = []

    area = np.linalg.norm(_vector_area(x), axis=1)
    size = np.max(np.linalg.norm(x - np.roll(x, 1, axis=1), axis=2), axis=1)
    degenerate = area <= 1e-12 * np.maximum(size, 1e-300) ** 2
    for i in np.nonzero(degenerate)[0]:
        issues.append(ShellShapeIssue(ids[i], "zero_area", "error", float(area[i]), 0.0,
                                      f"Shell element {ids[i]!r} has zero area (coincident or collinear nodes)."))
    ok = ~degenerate
    if not np.any(ok):
        return issues
    sub = np.nonzero(ok)[0]
    measures = shell_shape_measures(x[ok])
    k = x.shape[1]
    lo, hi = SHELL_QUAD_ANGLE_RANGE_DEG

    for j, i in enumerate(sub):
        eid = ids[i]
        angles = measures["inside_angles"][j]
        worst = float(angles.max())
        if worst >= SHELL_ANGLE_LIMIT_DEG - 1e-9:
            issues.append(ShellShapeIssue(
                eid, "inside_angle", "error", worst, SHELL_ANGLE_LIMIT_DEG,
                f"Shell element {eid!r} has an inside angle of {worst:.1f}°; it must be less than 180° ({_CLAUSE}). "
                f"Check the node order and the corner positions."))
        elif k == 4:
            out = angles[(angles < lo) | (angles > hi)]
            if out.size:
                bad = float(out[np.argmax(np.abs(out - 90.0))])
                issues.append(ShellShapeIssue(
                    eid, "inside_angle", "warning", bad, lo if bad < lo else hi,
                    f"Shell element {eid!r} has an inside angle of {bad:.1f}°, outside the range 45°–135° "
                    f"recommended for quadrilaterals ({_CLAUSE})."))

        aspect = float(measures["aspect_ratio"][j])
        if aspect > SHELL_ASPECT_LIMIT:
            issues.append(ShellShapeIssue(
                eid, "aspect_ratio", "error", aspect, SHELL_ASPECT_LIMIT,
                f"Shell element {eid!r} has an aspect ratio of {aspect:.2f}; it should not exceed 10 ({_CLAUSE})."))
        elif aspect > SHELL_ASPECT_WARN:
            issues.append(ShellShapeIssue(
                eid, "aspect_ratio", "warning", aspect, SHELL_ASPECT_WARN,
                f"Shell element {eid!r} has an aspect ratio of {aspect:.2f}; best results are obtained below 4 "
                f"({_CLAUSE})."))

        warp = float(measures["warping"][j])
        if warp > SHELL_WARP_LIMIT_DEG:
            issues.append(ShellShapeIssue(
                eid, "warping", "error", warp, SHELL_WARP_LIMIT_DEG,
                f"Shell element {eid!r} is warped: the largest angle between corner normals is {warp:.1f}°; it "
                f"should not exceed 45° ({_CLAUSE})."))
        elif warp > SHELL_WARP_WARN_DEG:
            issues.append(ShellShapeIssue(
                eid, "warping", "warning", warp, SHELL_WARP_WARN_DEG,
                f"Shell element {eid!r} is warped: the largest angle between corner normals is {warp:.1f}°; best "
                f"results are obtained below 30° ({_CLAUSE})."))
    return issues


def rotate_shell_resultants(
    forces: Any,
    axes: Any,
    direction: Any,
    flip_normal: Any = False,
) -> np.ndarray:
    """
    Express shell stress resultants in new in-plane axes 1'-2'-3'.

    The new axis 1' is the projection of the global vector ``direction`` on the element plane. The new axis 3' is the
    element's axis 3, or its opposite where ``flip_normal`` is true, and 2' = 3' x 1'. With the in-plane direction
    cosines T[a, i] = a_a . e_i (a = 1', 2'; i = 1, 2) and s = +1 or -1 for a kept or flipped normal:

    - membrane forces, a tensor: F' = T F T^T;
    - moments, a tensor that changes sign with the thickness coordinate (M = -integral of x3 sigma): M' = s T M T^T;
    - transverse shears, a vector along 3: V' = s T V.

    Parameters
    ----------
    forces : array_like (..., 8)
        Resultants in the element's 1-2-3 axes, ordered as ``SHELL_FORCE_KEYS``.
    axes : array_like (..., 3, 3)
        Element local axes (rows e1, e2, e3), from :func:`shell_local_axes`.
    direction : array_like (3,) or (..., 3)
        Global vector giving the new axis 1'. It must not be normal to the element plane.
    flip_normal : bool or array_like (...)
        Use -e3 as the new axis 3'.

    Returns
    -------
    numpy.ndarray (..., 8)
    """
    f = np.asarray(forces, dtype=float)
    r = np.asarray(axes, dtype=float)
    if f.shape[-1] != 8 or r.shape[-2:] != (3, 3):
        raise ValueError("forces must have shape (..., 8) and axes shape (..., 3, 3)")
    e1, e2, e3 = r[..., 0, :], r[..., 1, :], r[..., 2, :]
    d = np.broadcast_to(np.asarray(direction, dtype=float), e3.shape)
    d_len = np.linalg.norm(d, axis=-1)
    d_in = d - np.sum(d * e3, axis=-1, keepdims=True) * e3
    d_in_len = np.linalg.norm(d_in, axis=-1)
    if np.any(d_len <= 0.0) or np.any(d_in_len < SHELL_HORIZONTAL_SINE * d_len):
        raise ValueError("direction is zero or normal to the element plane; it cannot define an in-plane axis")
    a1 = d_in / d_in_len[..., None]
    sign = np.where(np.asarray(flip_normal, dtype=bool), -1.0, 1.0)
    sign = np.broadcast_to(sign, e3.shape[:-1])
    a2 = np.cross(sign[..., None] * e3, a1)

    t = np.empty(e3.shape[:-1] + (2, 2))
    t[..., 0, 0] = np.sum(a1 * e1, axis=-1)
    t[..., 0, 1] = np.sum(a1 * e2, axis=-1)
    t[..., 1, 0] = np.sum(a2 * e1, axis=-1)
    t[..., 1, 1] = np.sum(a2 * e2, axis=-1)

    def tensor(xx, yy, xy):
        m = np.empty(xx.shape + (2, 2))
        m[..., 0, 0], m[..., 1, 1], m[..., 0, 1], m[..., 1, 0] = xx, yy, xy, xy
        return np.einsum("...ai,...ij,...bj->...ab", t, m, t)

    fm = tensor(f[..., 0], f[..., 1], f[..., 2])
    mm = sign[..., None, None] * tensor(f[..., 3], f[..., 4], f[..., 5])
    vv = sign[..., None] * np.einsum("...ai,...i->...a", t, f[..., 6:8])
    out = np.empty(np.broadcast_shapes(f.shape, e3.shape[:-1] + (8,)))
    out[..., 0], out[..., 1], out[..., 2] = fm[..., 0, 0], fm[..., 1, 1], fm[..., 0, 1]
    out[..., 3], out[..., 4], out[..., 5] = mm[..., 0, 0], mm[..., 1, 1], mm[..., 0, 1]
    out[..., 6], out[..., 7] = vv[..., 0], vv[..., 1]
    return out


def _edges(nodes: Sequence[Any]) -> List[Tuple[Any, Any]]:
    k = len(nodes)
    return [(nodes[i], nodes[(i + 1) % k]) for i in range(k)]


def check_normal_consistency(
    connectivity: Sequence[Sequence[Any]],
    axes: Any,
    element_ids: Optional[Sequence[Any]] = None,
    required_normal: Optional[Any] = None,
    plane_tolerance_deg: float = SHELL_PLANE_TOLERANCE_DEG,
) -> List[ShellShapeIssue]:
    """
    Find shell elements whose normals (local axis 3) are inconsistent. Moments M11 and M22 change sign with the normal,
    so a mesh with flipped elements gives a moment field that looks discontinuous.

    - ``flipped_normal`` (warning): two elements share an edge and lie in one plane (normals within
      ``plane_tolerance_deg`` of parallel) but their normals point to opposite sides.
    - ``normal_direction`` (warning): with ``required_normal`` given (for example (0, 0, 1) for a floor), an element
      whose normal is more than ``plane_tolerance_deg`` from it.

    Parameters
    ----------
    connectivity : sequence of node-ID sequences, one per element (3 or 4 nodes each)
    axes : array_like (N, 3, 3)
        Element local axes from :func:`shell_local_axes`, in the order of ``connectivity``.
    """
    r = np.asarray(axes, dtype=float)
    ids = list(element_ids) if element_ids is not None else list(range(len(connectivity)))
    if r.shape != (len(connectivity), 3, 3) or len(ids) != len(connectivity):
        raise ValueError("connectivity, axes, and element_ids must describe the same elements")
    e3 = r[:, 2, :]
    cos_tol = math.cos(math.radians(plane_tolerance_deg))
    issues: List[ShellShapeIssue] = []

    edge_owner: Dict[frozenset, List[int]] = {}
    for i, nodes in enumerate(connectivity):
        for a, b in _edges(list(nodes)):
            edge_owner.setdefault(frozenset((a, b)), []).append(i)
    reported = set()
    for owners in edge_owner.values():
        for p in range(len(owners)):
            for q in range(p + 1, len(owners)):
                i, j = owners[p], owners[q]
                if (i, j) in reported:
                    continue
                dot = float(e3[i] @ e3[j])
                if dot < -cos_tol:
                    reported.add((i, j))
                    issues.append(ShellShapeIssue(
                        ids[j], "flipped_normal", "warning", math.degrees(math.acos(max(-1.0, min(1.0, dot)))),
                        180.0 - plane_tolerance_deg,
                        f"Shell elements {ids[i]!r} and {ids[j]!r} share an edge but their normals (local axis 3) "
                        f"point to opposite sides, so M11 and M22 change sign between them. Reverse the node order of "
                        f"one of them."))

    if required_normal is not None:
        req = np.asarray(required_normal, dtype=float)
        req = req / np.linalg.norm(req)
        dots = e3 @ req
        for i in np.nonzero(dots < cos_tol)[0]:
            ang = math.degrees(math.acos(max(-1.0, min(1.0, float(dots[i])))))
            issues.append(ShellShapeIssue(
                ids[i], "normal_direction", "warning", ang, plane_tolerance_deg,
                f"Shell element {ids[i]!r} has its normal (local axis 3) {ang:.1f}° from the required direction "
                f"{tuple(float(v) for v in req)}."))
    return issues


def average_shell_node_forces(
    connectivity: Sequence[Sequence[Any]],
    corner_forces: Sequence[Any],
    axes: Any,
    element_ids: Optional[Sequence[Any]] = None,
    direction: Optional[Any] = None,
    plane_tolerance_deg: float = SHELL_PLANE_TOLERANCE_DEG,
) -> Dict[Any, List[Any]]:
    """
    Average the corner values of shell resultants at each node, plane by plane.

    The elements at a node are grouped by plane: an element joins a group when its normal is within
    ``plane_tolerance_deg`` of parallel (either sense) to the normal of the group's first element. Each group is
    reported separately, so values are never averaged across a slab-wall junction. Within a group, every element's
    corner values are rotated with :func:`rotate_shell_resultants` into the group's common axes and then averaged:

    - axis 3: the normal of the group's first element (elements with the opposite normal are rotated with a flipped
      normal, and a warning names them);
    - axis 1: the projection of ``direction`` on each element's plane, or, without ``direction``, the local axis 1 of
      the group's first element.

    Parameters
    ----------
    connectivity : sequence of node-ID sequences, one per element
    corner_forces : sequence of arrays (k, 8), one per element, in element local axes and node order
    axes : array_like (N, 3, 3), element local axes from :func:`shell_local_axes`
    element_ids : sequence, optional (defaults to element indices)
    direction : array_like (3,), optional, global vector for the common axis 1

    Returns
    -------
    dict
        ``{node_id: [ShellNodeForces, ...]}``, one entry per plane group at the node.
    """
    from ..analysis_result.shell_result import ShellNodeForces, shell_forces_from_array

    r = np.asarray(axes, dtype=float)
    n_el = len(connectivity)
    ids = list(element_ids) if element_ids is not None else list(range(n_el))
    if r.shape != (n_el, 3, 3) or len(ids) != n_el or len(corner_forces) != n_el:
        raise ValueError("connectivity, corner_forces, axes, and element_ids must describe the same elements")
    cos_tol = math.cos(math.radians(plane_tolerance_deg))

    at_node: Dict[Any, List[Tuple[int, int]]] = {}
    for i, nodes in enumerate(connectivity):
        cf = np.asarray(corner_forces[i], dtype=float)
        if cf.shape != (len(nodes), 8):
            raise ValueError(f"corner_forces of element {ids[i]!r} must have shape ({len(nodes)}, 8)")
        for c, nid in enumerate(nodes):
            at_node.setdefault(nid, []).append((i, c))

    out: Dict[Any, List[Any]] = {}
    flipped_report: List[str] = []
    for nid, entries in at_node.items():
        groups: List[List[Tuple[int, int]]] = []
        for entry in entries:
            n_i = r[entry[0], 2]
            for g in groups:
                if abs(float(n_i @ r[g[0][0], 2])) >= cos_tol:
                    g.append(entry)
                    break
            else:
                groups.append([entry])

        node_out = []
        for g in groups:
            first = g[0][0]
            normal = r[first, 2]
            dvec = r[first, 0] if direction is None else np.asarray(direction, dtype=float)
            vals, flipped = [], []
            for i, c in g:
                flip = bool(r[i, 2] @ normal < 0.0)
                if flip:
                    flipped.append(ids[i])
                vals.append(rotate_shell_resultants(np.asarray(corner_forces[i], float)[c], r[i], dvec, flip))
            mean = np.mean(vals, axis=0)
            d_in = dvec - (dvec @ normal) * normal
            axis_1 = d_in / np.linalg.norm(d_in)
            node_out.append(ShellNodeForces(
                node_id=nid,
                element_ids=[ids[i] for i, _ in g],
                normal=tuple(float(v) for v in normal),
                axis_1=tuple(float(v) for v in axis_1),
                forces=shell_forces_from_array(mean),
                flipped_element_ids=flipped,
            ))
            if flipped:
                flipped_report.append(f"node {nid!r}: {flipped}")
        out[nid] = node_out

    if flipped_report:
        shown = "; ".join(flipped_report[:10]) + (" ..." if len(flipped_report) > 10 else "")
        warnings.warn(
            "Shell elements with flipped normals were averaged with their moments and shears rotated to the common "
            f"normal ({len(flipped_report)} node(s)): {shown}",
            stacklevel=2,
        )
    return out


# ── Model-level helpers ─────────────────────────────────────────────────────────────────────────────────────


def model_shell_axes(model: Any, element_ids: Optional[Sequence[Any]] = None) -> Dict[Any, np.ndarray]:
    """Local axes (3 x 3, rows e1, e2, e3) of the shell elements of a ``StructuralModel``, keyed by element ID.

    Triangles and quadrilaterals are each computed in one vectorized call of :func:`shell_local_axes`.
    """
    nodes = {n.id: n for n in model.nodes}
    wanted = None if element_ids is None else set(element_ids)
    by_count: Dict[int, List[Any]] = {3: [], 4: []}
    for el in model.shell_elements:
        if wanted is None or el.id in wanted:
            by_count[len(el.node_ids)].append(el)
    out: Dict[Any, np.ndarray] = {}
    for count, els in by_count.items():
        if not els:
            continue
        missing = [(el.id, nid) for el in els for nid in el.node_ids if nid not in nodes]
        if missing:
            raise ValueError(f"Shell elements reference missing nodes: {missing[:10]}")
        coords = np.array([[(nodes[nid].x, nodes[nid].y, nodes[nid].z) for nid in el.node_ids] for el in els])
        angle = np.array([el.axis_angle for el in els])
        ref = np.array([el.reference_vector if el.reference_vector is not None else (np.nan,) * 3 for el in els])
        axes = shell_local_axes(coords, angle, ref)
        out.update({el.id: axes[i] for i, el in enumerate(els)})
    return out


def model_shell_coordinates(model: Any) -> Dict[int, Tuple[List[Any], np.ndarray]]:
    """Coordinates of the shell elements of a model, grouped by node count: ``{k: (element_ids, coords (N, k, 3))}``.
    Elements with missing nodes are left out (validation reports them)."""
    nodes = {n.id: n for n in model.nodes}
    groups: Dict[int, Tuple[List[Any], List[Any]]] = {}
    for el in model.shell_elements:
        if any(nid not in nodes for nid in el.node_ids):
            continue
        ids, pts = groups.setdefault(len(el.node_ids), ([], []))
        ids.append(el.id)
        pts.append([(nodes[nid].x, nodes[nid].y, nodes[nid].z) for nid in el.node_ids])
    return {k: (ids, np.array(pts, dtype=float)) for k, (ids, pts) in groups.items()}


def check_model_shells(model: Any, required_normal: Optional[Any] = None) -> List[ShellShapeIssue]:
    """Shape checks (CSI §10.2.1) and normal consistency of all shell elements of a model."""
    issues: List[ShellShapeIssue] = []
    ok_ids: List[Any] = []
    for _, (ids, coords) in model_shell_coordinates(model).items():
        found = check_shell_shapes(coords, ids)
        issues.extend(found)
        zero = {i.element_id for i in found if i.check == "zero_area"}
        ok_ids.extend(eid for eid in ids if eid not in zero)
    if ok_ids:
        axes = model_shell_axes(model, ok_ids)
        by_id = {el.id: el for el in model.shell_elements}
        order = [eid for eid in ok_ids if eid in axes]
        issues.extend(check_normal_consistency(
            [by_id[eid].node_ids for eid in order], np.array([axes[eid] for eid in order]), order,
            required_normal=required_normal))
    return issues
