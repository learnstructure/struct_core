# struct_core

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green)](https://docs.pydantic.dev/)

**One Engineering Model. Many Engineering Tools.**

`struct_core` is a Pydantic v2–based Python package that defines the common data language for the structural engineering ecosystem. It is the single source of truth for engineering schemas consumed by [`fem2d`](https://github.com/learnstructure/fem-2d), [`structdyn`](https://github.com/learnstructure/structdyn), `aci318`, and `struct_draw`.

---

## Why This Exists

When building structural engineering software, the natural approach is to wire every tool directly to the solver.

A GUI constructs `fem2d.Structure` objects. An AI agent calls `structure.add_element()`. An ETABS importer walks the internal solver API.

This creates a fragile web where every tool is tightly coupled to every solver. When the solver changes, everything breaks.

**struct_core** solves this by providing a single, neutral engineering language that sits between all tools and all solvers:

```
Natural Language / GUI / ETABS / IFC / Excel / Optimization
                        │
                        ▼
                  struct_core
             (Pure Data + Validation)
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
       fem2d       structdyn        aci318
  (FE Assembly)  (Modal/Dynamics)  (RC Design)
                                       │
                                       ▼
                                  struct_draw
                               (Drawing Generation)
```

Every tool speaks one neutral engineering language. Solvers and design packages are free to evolve independently. The schema is the single source of truth.

---

## Features

- **Four-Subpackage Architecture** — Clean separation of concerns across the engineering lifecycle: input model, analysis outputs, design outputs, and detailing outputs.
- **Declarative Domain Models** — Data schemas with no solver logic and no design equations. The only computation is shared geometry (`struct_core.geometry`: shell local axes and shape checks), so that every package uses the same axes.
- **Pydantic v2 Validation** — Strong type checking, referential integrity (element → node/section, section → material, reinforcing-bar references → rebar materials), duplicate ID detection, and zero-length element checks.
- **JSON Serialization** — Full round-trip JSON and Python dict import/export with `to_json()`, `from_json()`, `save_json()`, and `load_json()`.
- **Sections Own Their Materials** — A section is the complete cross-section definition (geometry, material, and for reinforced concrete its bar materials and clear cover), as in ETABS / SAP2000. Elements reference only a section; `StructuralModel.material_of(element)` resolves the material.
- **Polymorphic Type System** — Discriminated unions for materials (`elastic`, `concrete`, `rebar`, `bilinear`), sections (`rectangular`, `circular`, `general`), elements (`beam`, `truss`, `spring`; shell elements in their own list), and analysis cases (`linear_static`, `nonlinear_static`, `modal`, `time_history`).
- **Full Project Lifecycle Container** — `Project` wraps `Metadata`, `StructuralModel`, `AnalysisResult`, `DesignResult`, and `DetailingResult` in one serializable object.
- **Lightweight Plugin Registry** — Register custom element types via `@ElementRegistry.register("custom_type")` without modifying core source code.
- **3D Ready** — Nodes carry `(x, y, z)` coordinates with `z=0.0` default, ensuring a clean upgrade path to full 3D support.

---

## Installation

### From Source (Developer Install)

```bash
git clone https://github.com/learnstructure/struct-schema.git
cd struct-schema
pip install -e .
```

### Requirements

- Python 3.9+
- pydantic >= 2.0.0
- numpy >= 1.20 (`struct_core.geometry`)

---

## Package Structure

```
struct_core/
├── structural_model/      # What the structure is
│   ├── units.py           #   Units, parse_units, conversion_factor
│   ├── nodes.py           #   Node
│   ├── materials.py       #   ElasticMaterial, ConcreteMaterial, RebarMaterial, BilinearMaterial
│   ├── sections.py        #   RectangularSection, CircularSection (SolidSection), GeneralSection
│   ├── elements.py        #   TrussElement, BeamElement, SpringElement
│   ├── shells.py          #   ShellSection, ShellElement (slabs and walls)
│   ├── groups.py          #   ObjectGroup (named selections of nodes, elements, and shells)
│   ├── supports.py        #   Support
│   ├── loads.py           #   PointLoad, DistributedLoad, AreaLoad, ShellLoad, LoadCase, LoadCombination
│   ├── mass_source.py     #   MassSource, MassSourceFactor
│   ├── analysis.py        #   LinearStaticAnalysis, ModalAnalysis, TimeHistoryAnalysis
│   ├── model.py           #   StructuralModel (get_material, get_section, section_of, material_of)
│   ├── migration.py       #   loads models saved with element material_id (before 0.3)
│   ├── validation.py      #   validate_structural_model
│   └── registry.py        #   ElementRegistry
├── analysis_result/       # How the structure responds (produced by fem2d, structdyn)
│   ├── node_result.py     #   NodeDisplacement, NodeReaction, NodeResult
│   ├── element_result.py  #   BeamSectionForce, ElementResult
│   ├── shell_result.py    #   ShellForces, ShellElementResult, ShellNodeForces
│   ├── modal_result.py    #   ModeShape, ModalResult
│   ├── time_history_result.py  # TimeHistoryResult
│   └── analysis_result.py #   AnalysisResult
├── design_result/         # What the code design produces (produced by aci318)
│   ├── code_check.py      #   CodeCheckResult
│   ├── material_design.py #   FlexureDesignResult, ShearDesignResult
│   ├── element_design.py  #   ElementDesignResult
│   ├── design_inputs.py   #   DesignInputs, AppliedDefault
│   └── design_result.py   #   DesignResult
├── detailing_result/      # What gets drawn and built (produced by aci318, consumed by struct_draw)
│   ├── rebar.py           #   Bar, RebarLayer, StirrupLayout, BarLayout
│   ├── anchorage.py       #   HookGeometry, LapSplice, Anchorage
│   ├── schedule.py        #   BarScheduleItem, BarSchedule
│   ├── element_detailing.py  # ElementDetailingResult
│   └── detailing_result.py   # DetailingResult
├── geometry/              # Shared geometry: shell local axes, shape checks, resultant rotation and averaging
├── project.py             # Project (top-level lifecycle container)
├── metadata.py            # Metadata
├── serialization.py       # to_json, from_json, save_json, load_json
└── base.py                # BaseSchemaModel, IDType aliases
```

---

## Unified Units Architecture

`struct_core` establishes a canonical unit authority for the entire structural engineering ecosystem via `Units`:

```python
from struct_core import Units, parse_units, conversion_factor

# 1. Flexible natural constructor (string, kwargs, or dict)
u1 = Units("kN, m")           # Metric: kN, m, s, C
u2 = Units("kip, in")         # US Customary: kip, in, s, F
u3 = Units("N, mm")           # Laboratory: N, mm, s, C

# 2. Automated physical properties & constants
print(u1.gravity_acceleration)      # 9.80665 m/s^2 (exact per length unit)
print(u2.gravity_acceleration)      # 386.0886 in/s^2
print(u1.consistent_mass_factor)    # 0.001 (kg -> kN*s^2/m)
print(u1.is_metric)                 # True
print(u2.is_us_customary)           # True

# 3. Unit conversions across packages
cf = conversion_factor("kN, m", "kip, in", "force")           # 0.224808943
cd = conversion_factor("kN, m", "kip, in", "weight_density")  # 3.6839e-6
```

All solvers (`fem2d`, `fem3d`), load generators (`struct_load`), CAE links (`struct_link`), and drawing modules (`struct_draw`) inspect active `model.units` or `project.metadata.units` directly, eliminating manual conversion errors.

---

## Quick Start

### Define a Portal Frame Model

```python
from struct_core.structural_model import (
    StructuralModel,
    Node, BeamElement,
    ElasticMaterial, RectangularSection,
    Support, LoadCase, PointLoad, DistributedLoad,
    LinearStaticAnalysis,
    validate_structural_model,
)
from struct_core import Project, Units, save_json

model = StructuralModel(
    units=Units("kN, m"),  # or string: units="kN, m"
    nodes=[
        Node(id=1, x=0.0, y=0.0),
        Node(id=2, x=0.0, y=4.0),
        Node(id=3, x=6.0, y=4.0),
        Node(id=4, x=6.0, y=0.0),
    ],
    materials=[
        ElasticMaterial(id="Steel", E=200e9, rho=7850.0),
    ],
    sections=[  # a section owns its material
        RectangularSection(id="Col",  b=0.30, h=0.30, material_id="Steel"),
        RectangularSection(id="Beam", b=0.25, h=0.45, material_id="Steel"),
    ],
    elements=[  # an element references only its section
        BeamElement(id=1, start_node=1, end_node=2, section_id="Col"),
        BeamElement(id=2, start_node=2, end_node=3, section_id="Beam"),
        BeamElement(id=3, start_node=3, end_node=4, section_id="Col"),
    ],
    supports=[
        Support.fixed(node_id=1),
        Support.fixed(node_id=4),
    ],
    load_cases=[
        LoadCase(
            id="GravityAndWind",
            point_loads=[PointLoad(node_id=2, fx=20e3)],
            element_loads=[DistributedLoad(element_id=2, wy=-15e3)],
        )
    ],
    analysis_cases=[
        LinearStaticAnalysis(id="A1", load_case_id="GravityAndWind"),
    ],
)

project = Project()
project.metadata.title = "2D Portal Frame"
project.metadata.author = "Engineer"
project.model = model
```

### Validate the Model

```python
from struct_core.structural_model import validate_structural_model

validate_structural_model(model)
# Raises StructuralValidationError clearly describing any issues
# before any solver is called.
```

### Save and Load as JSON

```python
from struct_core import save_json, load_json, Project

save_json(project, "portal.json", indent=2)
reloaded = load_json(Project, "portal.json")
```

### Run Analysis with fem2d

```python
from fem2d import model_from_core

structure = model_from_core(project)
structure.solve()
```

### Attach Analysis Results

```python
from struct_core.analysis_result import AnalysisResult, NodeResult, NodeDisplacement

result = AnalysisResult(
    analysis_case_id="A1",
    node_results={
        2: NodeResult(node_id=2, displacement=NodeDisplacement(ux=0.0005, uy=-0.0001)),
    },
)
project.analysis_results["A1"] = result
```

### Attach Design & Detailing Results (from aci318)

```python
from struct_core.design_result import DesignResult, ElementDesignResult, FlexureDesignResult
from struct_core.detailing_result import DetailingResult, ElementDetailingResult

project.design_results["ACI318"] = DesignResult(
    design_code="ACI 318-19",
    element_results={
        2: ElementDesignResult(
            element_id=2,
            flexure=FlexureDesignResult(
                required_steel_area=1.44, provided_steel_area=1.58,
                phi_mn=1800.0, mu=1450.0, dcr=0.806, passed=True,
            ),
            passed=True,
        )
    },
    governing_dcr=0.806,
    passed=True,
)

project.detailing_results["ACI318"] = DetailingResult(
    element_results={
        2: ElementDetailingResult(element_id=2, member_type="beam")
    }
)
```

---

## Schema Overview

### `structural_model` — Input Engineering Model

| Classes | Description |
|:---|:---|
| `Units` | Canonical engineering units specification and conversion authority |
| `Node` | 2D/3D node with coordinates and optional lumped mass |
| `ElasticMaterial`, `BilinearMaterial` | Linear and bilinear material models (with unit_weight and rho) |
| `ConcreteMaterial`, `RebarMaterial` | Reinforced-concrete materials: elastic for analysis (subclasses of `ElasticMaterial`) with their design strengths, concrete `fc` and rebar `fy` / `fu`, in the model stress unit |
| `RectangularSection`, `CircularSection`, `GeneralSection` | Cross-section definitions, each with its `material_id` (including effective shear areas `As2`, `As3` for Timoshenko beam analysis). Rectangular and circular sections may be reinforced concrete: `rebar_material_id` (longitudinal, fy), `transverse_rebar_material_id` (stirrups and ties, fyt) and clear `cover` |
| `TrussElement`, `BeamElement`, `SpringElement` | Structural element types (including end releases and `include_shear_deformation` flag); truss and beam elements reference a `section_id` |
| `ShellSection`, `ShellElement` | Slabs and walls: 3- or 4-node shell elements in `StructuralModel.shell_elements`, with sections in `StructuralModel.shell_sections` (`thickness`, optional `bending_thickness` / `effective_bending_thickness`, `behavior` `shell`/`membrane`/`plate`, `plate_theory` `thick`/`thin`). Local axes follow SAP2000 (`axis_angle`, `reference_vector`); see `struct_core.geometry` below. Rebar and cover fields are not yet on `ShellSection` |
| `ObjectGroup` | Named group (`id`) of nodes (`node_ids`), frame/truss/spring elements (`element_ids`), and shell elements (`shell_element_ids`) in `StructuralModel.groups`, resolved by `StructuralModel.get_group(group_id)` |
| `Support` | Boundary condition (pinned, fixed, roller, or custom spring stiffness) |
| `PointLoad`, `DistributedLoad`, `AreaLoad`, `GroundMotion` | Applied loads. `AreaLoad` is a floor pressure distributed to frame members, not a load on shell elements |
| `ShellLoad` | Uniform load per unit area on shell elements (`LoadCase.shell_loads`), along `local_3` or a global axis (`x`, `y`, `z`) |
| `LoadCase`, `LoadCombination` | Load grouping and factored combinations |
| `MassSource`, `MassSourceFactor` | Dynamic mass source specification (multipliers on dead/live load cases) |
| `LinearStaticAnalysis`, `ModalAnalysis`, `TimeHistoryAnalysis` | Analysis case definitions |
| `StructuralModel` | Top-level model container; `get_material`, `get_section`, `get_shell_section`, `get_shell_element`, `section_of(element)`, and `material_of(element or section)` resolve frame and shell references. Models saved with `material_id` on elements (before 0.3) are migrated on load: the material moves to the section, and a section shared by several materials is split (`COL`, `COL_C30`) |
| `ElementRegistry` | Plugin registry for custom element types |
| `classify_frame_members`, `frame_stories`, `frame_levels`, `vertical_axis`, `node_elevation` | Frame topology: column/beam/brace roles and story bands (`FrameStory`), shared by the analysis and design packages |

`Project.seismic_basis` (`SeismicDesignBasis`) records the seismic design basis: system, R, Ω0, Cd, I_e, Risk Category, S_DS, S_D1, S1, SDC, ρ, procedure, and lateral case IDs. The drift checks and the ACI 318 Chapter 18 frame checks read it. `elf_inputs` keeps the ELF generation inputs, so the weight-dependent story forces can be regenerated when members are resized.

### `analysis_result` — Analysis Outputs

| Classes | Description |
|:---|:---|
| `NodeDisplacement`, `NodeReaction`, `NodeResult` | Nodal displacements, rotations, and reactions |
| `BeamSectionForce`, `ElementResult` | Internal forces along beam elements (axial force tension positive). `envelope_results` keeps every enveloped combination's station forces in `ElementResult.combination_forces`, so design can check concurrent forces |
| `ModeShape`, `ModalResult` | Natural periods and mode shapes |
| `TimeHistoryResult` | Time-series dynamic response |
| `ShellForces`, `ShellElementResult`, `ShellNodeForces` | Shell stress resultants per unit length (`F11`, `F22`, `F12`, `M11`, `M22`, `M12`, `V13`, `V23`, names and signs of CSI Analysis Reference Manual §10.18) at Gauss points, element corners, and averaged at nodes per plane (`AnalysisResult.shell_results`, `shell_node_results`). Combined by `superpose_results` and `envelope_results` (`combination_corners`) |
| `AnalysisResult` | Container keyed by analysis case ID. `stiffness_basis` records the member stiffness (`gross` or `cracked`) and any run-level shear override (`shear` or `no_shear`), `moment_magnified` flags combinations with ACI 318-25 §6.6.4 second-order moment magnification, and `code_checks` holds frame-level analysis checks (slenderness, story drift, stability) |

### `geometry` — Shared Geometry of Shell Elements

The local axes of shell elements are computed only here, so that solvers, SAP2000/ETABS exchange, drawing, and design agree. Every array function works on N elements at once (coordinates of shape (N, k, 3), k = 3 or 4). See [`examples/shell_local_axes.py`](examples/shell_local_axes.py).

| Function | Description |
|:---|:---|
| `shell_local_axes` | Local axes 1-2-3 as an (N, 3, 3) array, SAP2000 27 convention (CSI Analysis Reference Manual §10.6–10.7). Orientation rules apply on the plane through j1, j2, j3 (axis 2 up, or +Y for horizontal elements, then `axis_angle` or `reference_vector`). Warped quadrilaterals beyond 0.81° (`struct_core.geometry.shell.SHELL_PLANAR_COSINE`) take axis 3 from the midpoints of opposite sides and project axis 2 onto that plane |
| `shell_areas`, `shell_normals` | Element areas and unit normals (axis 3) |
| `check_shell_shapes`, `shell_shape_measures`, `ShellShapeIssue` | Shape checks of CSI §10.2.1: warping (warn above 30°, refuse above 45°), inside angle (refuse at 180° or more; quadrilaterals warn outside 45°–135°), aspect ratio (warn above 4, refuse above 10) |
| `check_normal_consistency` | Flags neighbours with flipped normals (M11 and M22 change sign) and normals away from a required direction (+Z for a floor) |
| `rotate_shell_resultants` | Rotates the eight resultants (`SHELL_FORCE_KEYS`) into any in-plane direction, also with a flipped normal |
| `average_shell_node_forces` | Averages corner values at nodes by plane, never across a slab-wall junction |
| `shell_corner_weights` | Shares of an element's mass or load at its corners (CSI §10.11) |
| `model_shell_axes`, `model_shell_coordinates`, `check_model_shells` | Model-level helpers for the shell elements of a `StructuralModel` |

### `design_result` — Design Outputs

| Classes | Description |
|:---|:---|
| `CodeCheckResult` | Demand/capacity ratio (DCR) and pass/fail per code clause |
| `FlexureDesignResult`, `ShearDesignResult` | Strength design results |
| `ElementDesignResult` | Composite design summary per member |
| `DesignResult` | Container keyed by element ID. `system_checks` holds checks that belong to no single member (joints, story drift, stability); they count toward `governing_dcr`. `inputs` records what the design used |
| `DesignInputs`, `AppliedDefault` | Inputs of a design, in model units: copies of the designed materials and sections, the allowable soil bearing pressure and footing cover (`None` when foundations were not designed), and the defaults applied where the user gave no value |

### `detailing_result` — Detailing Outputs

| Classes | Description |
|:---|:---|
| `Bar`, `RebarLayer`, `BarLayout` | Rebar placement geometry |
| `StirrupLayout` | Shear reinforcement layout |
| `HookGeometry`, `LapSplice`, `Anchorage` | Anchorage and splice details |
| `BarScheduleItem`, `BarSchedule` | Cut-list and weight schedule |
| `ElementDetailingResult` | Complete detailing output per member |
| `DetailingResult` | Container keyed by element ID |

---

## Running Tests

```bash
pytest
```

---

## Ecosystem

| Package | Role |
|:---|:---|
| **struct_core** | Neutral engineering schema and validation (this package) |
| [fem2d](https://github.com/learnstructure/fem-2d) | 2D finite element solver — produces `AnalysisResult` |
| [structdyn](https://github.com/learnstructure/structdyn) | Structural dynamics: modal, response spectrum, time history — produces `AnalysisResult` |
| `aci318` | ACI 318 reinforced concrete design — produces `DesignResult` and `DetailingResult` |
| `struct_draw` | Drawing generation — consumes `DetailingResult` and `DesignResult`, outputs DXF/PDF |

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
