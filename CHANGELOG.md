# Changelog

All notable changes to `struct_core` are recorded in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/). The code of the paper is the git tag `v2.1-paper`.

## [Unreleased]

### Added
- `ObjectGroup` (`struct_core.structural_model.groups`) and `StructuralModel.groups` (with `StructuralModel.get_group`
  and `Project.groups` delegation), for named selections of nodes, frame elements, and shell elements (ROADMAP §1a).
  `validate_structural_model` checks unique group names and valid node, element, and shell-element references.
- `"other"` in `VALID_LOAD_TYPES` and `LOAD_TYPE_SYNONYMS`, so CSI load patterns with `DesignType=Other` keep their
  type across import and export without being re-guessed from the pattern name.
- Shell elements (slabs and walls), ROADMAP §4, plan in `fem3d/SHELL_PLAN.md` (M1):
  - `ShellSection` (membrane thickness, optional bending thickness, `behavior` shell/membrane/plate, `plate_theory`
    thick/thin) and `ShellElement` (3 or 4 nodes, `axis_angle`, `reference_vector`), in the new lists
    `StructuralModel.shell_sections` and `StructuralModel.shell_elements`, apart from frame sections and elements.
    Section and element IDs must be unique across frame and shell lists. `section_of` and `material_of` resolve shell
    elements; new lookups `get_shell_section` and `get_shell_element`.
  - `ShellLoad` in `LoadCase.shell_loads`: a uniform load per unit area along local axis 3 or a global axis, signed.
    `AreaLoad` is unchanged; its docstring now states that it is a floor load distributed to frame members.
  - Results: `ShellForces` (F11, F22, F12, M11, M22, M12, V13, V23; CSI Analysis Reference Manual §10.18 names and
    signs), `ShellElementResult` (Gauss points and corners), `ShellNodeForces` (averaged per plane group), and
    `AnalysisResult.shell_results` and `AnalysisResult.shell_node_results`. `superpose_results` and
    `envelope_results` combine them.
- `struct_core.geometry`: the single implementation of shell local axes (`shell_local_axes`, vectorized over N
  elements, SAP2000 convention of CSI §10.6–10.7), shape checks of CSI §10.2.1 (`check_shell_shapes`,
  `shell_shape_measures`: warping, inside angle, aspect ratio, with the clause in each message),
  `check_normal_consistency` (flipped neighbours, a required normal), `shell_areas`, `shell_normals`,
  `shell_corner_weights` (CSI §10.11 lumping), `rotate_shell_resultants` (into any in-plane direction, also with a
  flipped normal), `average_shell_node_forces` (by plane, never across a slab-wall junction; warns only for flipped
  normals), and model-level helpers `model_shell_axes`, `model_shell_coordinates`, and `check_model_shells`. Adds
  `numpy>=1.20` to `pyproject.toml`. Example: `examples/shell_local_axes.py`. Tests: `tests/test_shell_geometry.py`,
  `tests/test_shell_schema.py`.
- `validate_structural_model` checks shell references, duplicate IDs, and the shape errors of CSI §10.2.1.
- `convert_project_units` converts shell thicknesses, shell loads, and shell results.
- `STIFFNESS_MODIFIER_KEYS`: the keys of `BeamElement.stiffness_modifiers` (A, As2, As3, J, I2, I3, mass, weight),
  in the order of the CSI frame modifier array. fem2d, fem3d, and struct_link use it.

### Changed
- `geometry.shell_local_axes`: warped quadrilaterals now get the axes SAP2000 27 gives them, which the CSI manual
  does not state (measured through the API, fem3d/SHELL_PLAN.md M6). The orientation rules (default, reference
  vector, angle) apply to the plane through j1, j2, j3; the element then takes axis 3 from the midpoints of
  opposite sides and axis 2 as the projection of the first axis 2 on that plane. Quadrilaterals whose two normals
  are within 0.81 degrees (`struct_core.geometry.shell.SHELL_PLANAR_COSINE` = 1 - 1e-4, measured) keep the plane
  through j1, j2, j3. Flat elements and triangles are unchanged; the axes of 20 test panels and of the elements of
  SAP2000's own verification models equal SAP2000's to round-off (`struct_link/tests/test_sap2000_shells.py`). A
  cyclic renumbering keeps axis 3 of a warped element but may turn axes 1 and 2, as in SAP2000. Nodes j1, j2, j3 on
  a line are refused.
- **Breaking:** `BeamElement.stiffness_modifiers` refuses keys outside `STIFFNESS_MODIFIER_KEYS`. A misspelled key
  was ignored by the solvers, and fem2d also accepted the non-canonical keys `I` and `As`; no package produced them.
