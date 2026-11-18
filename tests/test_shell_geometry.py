"""
Tests of struct_core.geometry for shell elements: local axes (CSI Analysis Reference Manual §10.6–10.7), shape
checks (§10.2.1), corner weights (§10.11), rotation and nodal averaging of stress resultants (§10.18 names).
"""

import math
import warnings

import numpy as np
import pytest

from struct_core.geometry import (
    SHELL_HORIZONTAL_SINE,
    average_shell_node_forces,
    check_normal_consistency,
    check_shell_shapes,
    rotate_shell_resultants,
    shell_areas,
    shell_corner_weights,
    shell_local_axes,
    shell_shape_measures,
)

SQUARE = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]])


def axes_of(pts, **kw):
    return shell_local_axes(np.asarray(pts, float)[None], **kw)[0]


def assert_triad(r):
    assert np.allclose(r @ r.T, np.eye(3), atol=1e-12)
    assert np.allclose(np.cross(r[0], r[1]), r[2], atol=1e-12)


# ── Default axes (§10.6.1–10.6.2) ────────────────────────────────────────────────────────────────────────────


def test_horizontal_counterclockwise_floor_has_global_axes():
    r = axes_of(SQUARE)
    assert np.allclose(r, np.eye(3))


def test_horizontal_clockwise_floor_has_downward_normal_and_axis2_along_y():
    r = axes_of(SQUARE[::-1])
    assert np.allclose(r[2], [0, 0, -1])
    assert np.allclose(r[1], [0, 1, 0])
    assert np.allclose(r[0], [-1, 0, 0])
    assert_triad(r)


def test_vertical_wall_in_xz_plane():
    # j1-j2-j3 counterclockwise seen from -Y: normal -Y; axis 2 up; axis 1 horizontal
    r = axes_of([[0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1]])
    assert np.allclose(r[2], [0, -1, 0])
    assert np.allclose(r[1], [0, 0, 1])
    assert np.allclose(r[0], [1, 0, 0])


def test_vertical_wall_in_yz_plane():
    r = axes_of([[0, 0, 0], [0, 1, 0], [0, 1, 1], [0, 0, 1]])
    assert np.allclose(r[2], [1, 0, 0])
    assert np.allclose(r[1], [0, 0, 1])
    assert np.allclose(r[0], [0, 1, 0])


def test_sloped_roof_axis2_angle_with_vertical_equals_axis3_angle_with_horizontal():
    a = math.radians(30.0)
    c, s = math.cos(a), math.sin(a)
    r = axes_of([[0, 0, 0], [1, 0, 0], [1, c, s], [0, c, s]])
    assert np.allclose(r[2], [0, -s, c])
    assert np.allclose(r[1], [0, c, s])   # up the slope
    assert np.allclose(r[0], [1, 0, 0])   # horizontal
    # §10.6.2: local 2 makes the same angle with the vertical as local 3 makes with the horizontal plane
    assert math.isclose(math.acos(r[1] @ [0, 0, 1]), math.acos(math.hypot(r[2][0], r[2][1])), rel_tol=1e-12)


@pytest.mark.parametrize("factor, horizontal", [(0.5, True), (2.0, False)])
def test_nearly_horizontal_element_on_both_sides_of_the_tolerance(factor, horizontal):
    sine = factor * SHELL_HORIZONTAL_SINE
    theta = math.asin(sine)
    # a square tilted about the global Y axis: it rises along +X
    pts = [[0, 0, 0], [math.cos(theta), 0, math.sin(theta)], [math.cos(theta), 1, math.sin(theta)], [0, 1, 0]]
    r = axes_of(pts)
    assert math.isclose(math.hypot(r[2][0], r[2][1]), sine, rel_tol=1e-9)
    if horizontal:
        # treated as horizontal: axis 2 is +Y (already in the element plane here)
        assert np.allclose(r[1], [0, 1, 0], atol=1e-12)
    else:
        # not horizontal: the 3-2 plane is vertical and axis 2 points up the slope, nearly +X
        assert r[1][2] > 0 and abs(r[1][1]) < 1e-12
        assert np.allclose(r[1], [math.cos(theta), 0, math.sin(theta)], atol=1e-12)
    assert_triad(r)


def test_triangle_normal_and_axes():
    r = axes_of([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    assert np.allclose(r, np.eye(3))
    r = axes_of([[0, 0, 0], [0, 1, 0], [1, 0, 0]])
    assert np.allclose(r[2], [0, 0, -1])


def test_quadrilateral_plane_joins_midpoints_of_opposite_sides():
    # A warped quadrilateral: the normal is the cross product of the midpoint vectors (§10.6.1)
    pts = np.array([[0, 0, 0], [2, 0, 0.3], [2.2, 1.5, 0], [0, 1, 0.2]])
    mid = 0.5 * (pts + np.roll(pts, -1, axis=0))
    n = np.cross(mid[1] - mid[3], mid[2] - mid[0])
    assert np.allclose(axes_of(pts)[2], n / np.linalg.norm(n))


# ── Angle and reference vector (§10.6.3, §10.7) ─────────────────────────────────────────────────────────────


def test_axis_angle_rotates_axes_1_and_2_counterclockwise_about_3():
    r = axes_of(SQUARE, axis_angle=30.0)
    c, s = math.cos(math.radians(30)), math.sin(math.radians(30))
    assert np.allclose(r[0], [c, s, 0])
    assert np.allclose(r[1], [-s, c, 0])
    assert np.allclose(r[2], [0, 0, 1])


def test_reference_vector_sets_axis_2():
    r = axes_of(SQUARE, reference_vector=(1.0, 1.0, 0.3))
    q = 1 / math.sqrt(2)
    assert np.allclose(r[1], [q, q, 0])
    assert np.allclose(r[0], [q, -q, 0])
    assert_triad(r)


def test_reference_vector_then_angle():
    r = axes_of(SQUARE, reference_vector=(1.0, 0.0, 0.0), axis_angle=90.0)
    # reference: axis 2 = +X, axis 1 = -Y; then 90 degrees about +Z: axis 1 = +X, axis 2 = +Y
    assert np.allclose(r, np.eye(3), atol=1e-12)


def test_reference_vector_parallel_to_normal_is_refused():
    with pytest.raises(ValueError, match="parallel to local axis 3"):
        axes_of(SQUARE, reference_vector=(0.0, 0.0, 1.0))


def test_nan_reference_rows_keep_default_axes_in_a_vectorized_call():
    coords = np.stack([SQUARE, SQUARE])
    ref = np.array([[np.nan] * 3, [1.0, 0.0, 0.0]])
    r = shell_local_axes(coords, [0.0, 0.0], ref)
    assert np.allclose(r[0], np.eye(3))
    assert np.allclose(r[1][1], [1, 0, 0])


def test_vectorized_axes_equal_one_at_a_time():
    rng = np.random.default_rng(4)
    coords = SQUARE[None] * rng.uniform(0.5, 2.0, (50, 1, 3)) + rng.normal(0, 0.05, (50, 4, 3))
    # random rigid rotations, so that horizontal, vertical, and sloped elements all occur
    rot = np.linalg.qr(rng.normal(size=(50, 3, 3)))[0]
    coords = np.einsum("nij,nkj->nki", rot, coords)
    angles = rng.uniform(-180, 180, 50)
    all_at_once = shell_local_axes(coords, angles)
    for i in range(50):
        assert np.allclose(all_at_once[i], shell_local_axes(coords[i:i + 1], angles[i])[0])
        assert_triad(all_at_once[i])


def test_cyclic_renumbering_keeps_the_axes():
    pts = np.array([[0, 0, 0], [2, 0.1, 0], [2.3, 1.4, 0.4], [-0.2, 1.1, 0.1]])
    base = axes_of(pts)
    for shift in (1, 2, 3):
        assert np.allclose(axes_of(np.roll(pts, shift, axis=0)), base)


def test_zero_area_is_refused():
    with pytest.raises(ValueError, match="zero area"):
        axes_of([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]])


def test_coordinates_must_be_batched():
    with pytest.raises(ValueError, match=r"\(N, k, 3\)"):
        shell_local_axes(SQUARE)


# ── Shape checks (§10.2.1) ──────────────────────────────────────────────────────────────────────────────────


def test_good_square_has_no_findings():
    assert check_shell_shapes(SQUARE[None]) == []


def test_warping_measure_matches_hand_calculation():
    # Lifting one corner by h: the largest angle is between the corner normals at j2 and j4, (0,-h,1) and (-h,0,1)
    h = 0.4
    pts = np.array([[0, 0, 0], [1, 0, 0], [1, 1, h], [0, 1, 0]])
    expected = math.degrees(math.acos(1.0 / (1.0 + h * h)))
    assert math.isclose(shell_shape_measures(pts[None])["warping"][0], expected, rel_tol=1e-12)


@pytest.mark.parametrize("angle, severity", [(20.0, None), (35.0, "warning"), (50.0, "error")])
def test_warping_limits(angle, severity):
    h = math.sqrt(1.0 / math.cos(math.radians(angle)) - 1.0)  # warping angle = acos(1 / (1 + h^2))
    pts = np.array([[0, 0, 0], [1, 0, 0], [1, 1, h], [0, 1, 0]])
    found = [i for i in check_shell_shapes(pts[None], ["W1"]) if i.check == "warping"]
    if severity is None:
        assert found == []
    else:
        assert len(found) == 1 and found[0].severity == severity
        assert "§10.2.1" in found[0].message and found[0].element_id == "W1"


def test_reentrant_corner_is_refused_without_a_warping_finding():
    pts = np.array([[0, 0, 0], [2, 0, 0], [1, 0.2, 0], [0, 1, 0]])
    found = check_shell_shapes(pts[None])
    assert [(i.check, i.severity) for i in found] == [("inside_angle", "error")]
    assert found[0].value > 180.0 and "§10.2.1" in found[0].message


def test_inside_angle_warning_outside_45_to_135_degrees():
    skew = math.radians(40.0)
    pts = np.array([[0, 0, 0], [1, 0, 0], [1 + math.cos(skew), math.sin(skew), 0], [math.cos(skew), math.sin(skew), 0]])
    found = check_shell_shapes(pts[None])
    assert [(i.check, i.severity) for i in found] == [("inside_angle", "warning")]
    assert math.isclose(found[0].value, 140.0, abs_tol=1e-9) or math.isclose(found[0].value, 40.0, abs_tol=1e-9)


def test_triangles_are_not_held_to_the_quadrilateral_angle_range():
    # a 30-60-90 triangle: aspect ratio 2, no finding
    assert check_shell_shapes(np.array([[[0, 0, 0], [math.sqrt(3), 0, 0], [0, 1, 0]]])) == []


@pytest.mark.parametrize("length, severity", [(3.5, None), (5.0, "warning"), (12.0, "error")])
def test_aspect_ratio_limits(length, severity):
    pts = np.array([[0, 0, 0], [length, 0, 0], [length, 1, 0], [0, 1, 0]])
    found = check_shell_shapes(pts[None])
    assert [i.severity for i in found if i.check == "aspect_ratio"] == ([] if severity is None else [severity])
    assert math.isclose(shell_shape_measures(pts[None])["aspect_ratio"][0], length)


def test_degenerate_element_is_one_error():
    found = check_shell_shapes(np.array([[[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]]]), ["Z"])
    assert [(i.element_id, i.check, i.severity) for i in found] == [("Z", "zero_area", "error")]


# ── Corner weights and areas (§10.11) ───────────────────────────────────────────────────────────────────────


def test_corner_weights_rectangle_and_triangle():
    rect = np.array([[0, 0, 0], [3, 0, 0], [3, 2, 0], [0, 2, 0]])
    assert np.allclose(shell_corner_weights(rect[None]), 0.25)
    assert np.allclose(shell_corner_weights(np.array([[[0, 0, 0], [3, 0, 0], [0, 2, 0]]])), 1 / 3)
    assert math.isclose(shell_areas(rect[None])[0], 6.0)


def test_corner_weights_of_a_trapezoid_follow_the_consistent_mass_diagonal():
    # Trapezoid with parallel sides 2 (y = 0) and 1 (y = 1): |J| = (3 - eta) / 8. By hand, the diagonal terms
    # int N_i^2 |J| dxi deta are 7/36 at the corners of the long side and 5/36 at those of the short side.
    pts = np.array([[0, 0, 0], [2, 0, 0], [1.5, 1, 0], [0.5, 1, 0]])
    w = shell_corner_weights(pts[None])[0]
    assert np.allclose(w, np.array([7, 7, 5, 5]) / 24.0)
    assert math.isclose(w.sum(), 1.0)


# ── Rotation of resultants ──────────────────────────────────────────────────────────────────────────────────

F = np.array([3.0, -1.0, 0.7, 2.0, 0.5, -0.4, 1.2, -0.3])


def test_rotation_to_own_axis_1_is_identity():
    r = np.eye(3)
    assert np.allclose(rotate_shell_resultants(F, r, r[0]), F)


def test_rotation_by_90_degrees():
    r = np.eye(3)
    out = rotate_shell_resultants(F, r, [0, 1, 0])
    f11, f22, f12, m11, m22, m12, v13, v23 = F
    assert np.allclose(out, [f22, f11, -f12, m22, m11, -m12, v23, -v13])


def test_rotation_keeps_tensor_invariants():
    r = np.eye(3)
    for deg in (17.0, 63.0, 145.0):
        a = math.radians(deg)
        out = rotate_shell_resultants(F, r, [math.cos(a), math.sin(a), 0.4])
        for i in (0, 3):  # membrane and moment tensors
            assert math.isclose(out[i] + out[i + 1], F[i] + F[i + 1], abs_tol=1e-12)
            assert math.isclose(out[i] * out[i + 1] - out[i + 2] ** 2, F[i] * F[i + 1] - F[i + 2] ** 2, abs_tol=1e-12)
        assert math.isclose(math.hypot(out[6], out[7]), math.hypot(F[6], F[7]), abs_tol=1e-12)


def test_rotation_with_flipped_normal():
    r = np.eye(3)
    out = rotate_shell_resultants(F, r, [1, 0, 0], flip_normal=True)
    # New axes: 1' = 1, 3' = -3, 2' = -2, so T = diag(1, -1) and s = -1: F' = T F T, M' = -T M T, V' = -T V
    f11, f22, f12, m11, m22, m12, v13, v23 = F
    assert np.allclose(out, [f11, f22, -f12, -m11, -m22, m12, -v13, v23])
    back = rotate_shell_resultants(out, np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1.0]]), [1, 0, 0], flip_normal=True)
    assert np.allclose(back, F)


def test_flipped_element_reports_the_same_physical_state():
    # A plate bent so that the bottom fibres along X are in tension. Element A (normal +Z) has M11 = +1.
    # Element B is the same square numbered clockwise: normal -Z, axis 1 = -X; its bottom (negative x3) is the top
    # of A, so B reports M11 = -1. Rotating B to A's axes with a flipped normal recovers M11 = +1.
    ra = axes_of(SQUARE)
    rb = axes_of(SQUARE[::-1])
    fa = np.array([0, 0, 0, 1.0, 0, 0, 0, 0])
    fb = np.array([0, 0, 0, -1.0, 0, 0, 0, 0])
    assert np.allclose(rotate_shell_resultants(fb, rb, ra[0], flip_normal=True), fa)


def test_rotation_direction_normal_to_plane_is_refused():
    with pytest.raises(ValueError, match="normal to the element plane"):
        rotate_shell_resultants(F, np.eye(3), [0, 0, 1])


def test_rotation_is_vectorized():
    rng = np.random.default_rng(1)
    forces = rng.normal(size=(7, 4, 8))
    axes = np.broadcast_to(np.eye(3), (7, 4, 3, 3))
    out = rotate_shell_resultants(forces, axes, [0, 1, 0])
    assert out.shape == (7, 4, 8)
    assert np.allclose(out[3, 2], rotate_shell_resultants(forces[3, 2], np.eye(3), [0, 1, 0]))


# ── Normal consistency and nodal averaging ──────────────────────────────────────────────────────────────────


def two_squares(flip_second=False):
    coords = np.array([SQUARE, SQUARE + [1, 0, 0]])
    conn = [[1, 2, 5, 4], [2, 3, 6, 5]]
    if flip_second:
        coords[1] = coords[1][::-1]
        conn[1] = conn[1][::-1]
    return conn, coords


def test_normal_consistency_flags_a_flipped_neighbour_and_the_required_direction():
    conn, coords = two_squares(flip_second=True)
    axes = shell_local_axes(coords)
    issues = check_normal_consistency(conn, axes, ["A", "B"], required_normal=(0, 0, 1))
    checks = sorted((i.check, i.element_id) for i in issues)
    assert checks == [("flipped_normal", "B"), ("normal_direction", "B")]
    assert all(i.severity == "warning" for i in issues)
    conn, coords = two_squares()
    assert check_normal_consistency(conn, shell_local_axes(coords), required_normal=(0, 0, 1)) == []


def test_slab_wall_junction_is_not_flagged():
    coords = np.array([SQUARE, [[0, 0, 0], [1, 0, 0], [1, 0, -1], [0, 0, -1]]])
    conn = [[1, 2, 3, 4], [1, 2, 6, 5]]
    assert check_normal_consistency(conn, shell_local_axes(coords)) == []


def test_average_rotates_each_element_into_common_axes():
    # Physical state: membrane force 1 along global X. Element A has default axes (F11 = 1); element B has
    # axis_angle 90 (axis 1 = +Y), so it reports F22 = 1.
    conn, coords = two_squares()
    axes = shell_local_axes(coords, [0.0, 90.0])
    fa = np.tile([1.0, 0, 0, 0, 0, 0, 0, 0], (4, 1))
    fb = np.tile([0, 1.0, 0, 0, 0, 0, 0, 0], (4, 1))
    out = average_shell_node_forces(conn, [fa, fb], axes, ["A", "B"])
    shared = out[2]
    assert len(shared) == 1 and shared[0].element_ids == ["A", "B"]
    assert math.isclose(shared[0].forces.F11, 1.0) and abs(shared[0].forces.F22) < 1e-12
    assert np.allclose(shared[0].axis_1, [1, 0, 0])
    # a global direction rotates every group
    out_y = average_shell_node_forces(conn, [fa, fb], axes, ["A", "B"], direction=(0, 1, 0))
    assert math.isclose(out_y[2][0].forces.F22, 1.0)


def test_average_never_mixes_a_slab_and_a_wall():
    coords = np.array([SQUARE, [[0, 0, 0], [1, 0, 0], [1, 0, -1], [0, 0, -1]]])
    conn = [[1, 2, 3, 4], [1, 2, 6, 5]]
    axes = shell_local_axes(coords)
    fs = np.tile([0, 0, 0, 5.0, 0, 0, 0, 0], (4, 1))
    fw = np.tile([0, 0, 0, -2.0, 0, 0, 0, 0], (4, 1))
    out = average_shell_node_forces(conn, [fs, fw], axes, ["S", "W"])
    groups = out[1]
    assert [g.element_ids for g in groups] == [["S"], ["W"]]
    assert [g.forces.M11 for g in groups] == [5.0, -2.0]
    # the wall hangs below the slab edge (j1-j2-j3 counterclockwise seen from +Y)
    assert np.allclose(groups[0].normal, [0, 0, 1]) and np.allclose(groups[1].normal, [0, 1, 0])


def test_average_with_a_flipped_element_warns_and_keeps_the_physical_sign():
    conn, coords = two_squares(flip_second=True)
    axes = shell_local_axes(coords)
    fa = np.tile([0, 0, 0, 1.0, 0, 0, 0, 0], (4, 1))
    fb = np.tile([0, 0, 0, -1.0, 0, 0, 0, 0], (4, 1))  # same physical state, flipped element
    with pytest.warns(UserWarning, match="flipped normals"):
        out = average_shell_node_forces(conn, [fa, fb], axes, ["A", "B"])
    g = out[2][0]
    assert g.flipped_element_ids == ["B"] and math.isclose(g.forces.M11, 1.0)


def test_average_without_flips_does_not_warn():
    conn, coords = two_squares()
    axes = shell_local_axes(coords)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        average_shell_node_forces(conn, [np.zeros((4, 8)), np.zeros((4, 8))], axes)
