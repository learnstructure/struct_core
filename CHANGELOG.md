# Changelog

All notable changes to `struct_core` are recorded in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/). The code of the paper is the git tag `v2.1-paper`.

## [Unreleased]

### Added
- `STIFFNESS_MODIFIER_KEYS`: the keys of `BeamElement.stiffness_modifiers` (A, As2, As3, J, I2, I3, mass, weight),
  in the order of the CSI frame modifier array. fem2d, fem3d, and struct_link use it.

### Changed
- **Breaking:** `BeamElement.stiffness_modifiers` refuses keys outside `STIFFNESS_MODIFIER_KEYS`. A misspelled key
  was ignored by the solvers, and fem2d also accepted the non-canonical keys `I` and `As`; no package produced them.
