# Changelog

All notable changes to `struct_core` are recorded in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/). The code of the paper is the git tag `v2.1-paper`.

## [Unreleased]

### Added
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
  elements, SAP2000 convention of CSI §10.6–10.7), shape checks of CSI §10.2.1 (`check_shell_shapes`: warping,
  inside angle, aspect ratio, with the clause in each message), `check_normal_consistency` (flipped neighbours, a
  required normal), `shell_corner_weights` (CSI §10.11 lumping), `rotate_shell_resultants` (into any in-plane
  direction, also with a flipped normal), `average_shell_node_forces` (by plane, never across a slab-wall junction;
  warns only for flipped normals), and model-level helpers `model_shell_axes` and `check_model_shells`.
- `validate_structural_model` checks shell references, duplicate IDs, and the shape errors of CSI §10.2.1.
- `convert_project_units` converts shell thicknesses, shell loads, and shell results.
- `STIFFNESS_MODIFIER_KEYS`: the keys of `BeamElement.stiffness_modifiers` (A, As2, As3, J, I2, I3, mass, weight),
  in the order of the CSI frame modifier array. fem2d, fem3d, and struct_link use it.

### Changed
- **Breaking:** `BeamElement.stiffness_modifiers` refuses keys outside `STIFFNESS_MODIFIER_KEYS`. A misspelled key
  was ignored by the solvers, and fem2d also accepted the non-canonical keys `I` and `As`; no package produced them.
