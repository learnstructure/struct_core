"""
struct_core.geometry
====================

Canonical geometry shared by every package: the local axes of shell elements, their shape checks, and the rotation
and nodal averaging of shell stress resultants. Axes are computed here and nowhere else.
"""

from .shell import (
    SHELL_ASPECT_LIMIT,
    SHELL_ASPECT_WARN,
    SHELL_ANGLE_LIMIT_DEG,
    SHELL_FORCE_KEYS,
    SHELL_HORIZONTAL_SINE,
    SHELL_PLANE_TOLERANCE_DEG,
    SHELL_QUAD_ANGLE_RANGE_DEG,
    SHELL_WARP_LIMIT_DEG,
    SHELL_WARP_WARN_DEG,
    ShellShapeIssue,
    average_shell_node_forces,
    check_model_shells,
    check_normal_consistency,
    check_shell_shapes,
    model_shell_axes,
    model_shell_coordinates,
    rotate_shell_resultants,
    shell_areas,
    shell_corner_weights,
    shell_local_axes,
    shell_normals,
    shell_shape_measures,
)

__all__ = [
    "SHELL_ASPECT_LIMIT",
    "SHELL_ASPECT_WARN",
    "SHELL_ANGLE_LIMIT_DEG",
    "SHELL_FORCE_KEYS",
    "SHELL_HORIZONTAL_SINE",
    "SHELL_PLANE_TOLERANCE_DEG",
    "SHELL_QUAD_ANGLE_RANGE_DEG",
    "SHELL_WARP_LIMIT_DEG",
    "SHELL_WARP_WARN_DEG",
    "ShellShapeIssue",
    "average_shell_node_forces",
    "check_model_shells",
    "check_normal_consistency",
    "check_shell_shapes",
    "model_shell_axes",
    "model_shell_coordinates",
    "rotate_shell_resultants",
    "shell_areas",
    "shell_corner_weights",
    "shell_local_axes",
    "shell_normals",
    "shell_shape_measures",
]
