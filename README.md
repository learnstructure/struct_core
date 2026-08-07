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
- **Declarative Domain Models** — Pure data schemas with no solver logic, no matrix math, and no design equations.
- **Pydantic v2 Validation** — Strong type checking, referential integrity (missing node/material/section references), duplicate ID detection, and zero-length element checks.
- **JSON Serialization** — Full round-trip JSON and Python dict import/export with `to_json()`, `from_json()`, `save_json()`, and `load_json()`.
- **Polymorphic Type System** — Discriminated unions for materials (`elastic`, `bilinear`), sections (`rectangular`, `circular`, `general`), elements (`beam`, `truss`, `spring`), and analysis cases (`linear_static`, `nonlinear_static`, `modal`, `time_history`).
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

---

## Package Structure

```
struct_core/
├── structural_model/      # What the structure is
│   ├── nodes.py           #   Node
│   ├── materials.py       #   ElasticMaterial, BilinearMaterial
│   ├── sections.py        #   RectangularSection, CircularSection, GeneralSection
│   ├── elements.py        #   TrussElement, BeamElement, SpringElement
│   ├── supports.py        #   Support
│   ├── loads.py           #   PointLoad, DistributedLoad, LoadCase, LoadCombination
│   ├── analysis.py        #   LinearStaticAnalysis, ModalAnalysis, TimeHistoryAnalysis
│   ├── model.py           #   StructuralModel
│   ├── validation.py      #   validate_structural_model
│   └── registry.py        #   ElementRegistry
├── analysis_result/       # How the structure responds (produced by fem2d, structdyn)
│   ├── node_result.py     #   NodeDisplacement, NodeReaction, NodeResult
│   ├── element_result.py  #   BeamSectionForce, ElementResult
│   ├── modal_result.py    #   ModeShape, ModalResult
│   ├── time_history_result.py  # TimeHistoryResult
│   └── analysis_result.py #   AnalysisResult
├── design_result/         # What the code design produces (produced by aci318)
│   ├── code_check.py      #   CodeCheckResult
│   ├── material_design.py #   FlexureDesignResult, ShearDesignResult
│   ├── element_design.py  #   ElementDesignResult
│   └── design_result.py   #   DesignResult
├── detailing_result/      # What gets drawn and built (produced by aci318, consumed by struct_draw)
│   ├── rebar.py           #   Bar, RebarLayer, StirrupLayout, BarLayout
│   ├── anchorage.py       #   HookGeometry, LapSplice, Anchorage
│   ├── schedule.py        #   BarScheduleItem, BarSchedule
│   ├── element_detailing.py  # ElementDetailingResult
│   └── detailing_result.py   # DetailingResult
├── project.py             # Project (top-level lifecycle container)
├── metadata.py            # Metadata, Units
├── serialization.py       # to_json, from_json, save_json, load_json
└── base.py                # BaseSchemaModel, IDType aliases
```

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
from struct_core import Project, save_json

model = StructuralModel(
    nodes=[
        Node(id=1, x=0.0, y=0.0),
        Node(id=2, x=0.0, y=4.0),
        Node(id=3, x=6.0, y=4.0),
        Node(id=4, x=6.0, y=0.0),
    ],
    materials=[
        ElasticMaterial(id="Steel", E=200e9, rho=7850.0),
    ],
    sections=[
        RectangularSection(id="Col",  b=0.30, h=0.30),
        RectangularSection(id="Beam", b=0.25, h=0.45),
    ],
    elements=[
        BeamElement(id=1, start_node=1, end_node=2, material_id="Steel", section_id="Col"),
        BeamElement(id=2, start_node=2, end_node=3, material_id="Steel", section_id="Beam"),
        BeamElement(id=3, start_node=3, end_node=4, material_id="Steel", section_id="Col"),
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
from fem2d import from_schema

structure = from_schema(project)
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
| `Node` | 2D/3D node with coordinates and optional lumped mass |
| `ElasticMaterial`, `BilinearMaterial` | Linear and bilinear material models |
| `RectangularSection`, `CircularSection`, `GeneralSection` | Cross-section definitions |
| `TrussElement`, `BeamElement`, `SpringElement` | Structural element types |
| `Support` | Boundary condition (pinned, fixed, roller, or custom spring stiffness) |
| `PointLoad`, `DistributedLoad`, `GroundMotion` | Applied loads |
| `LoadCase`, `LoadCombination` | Load grouping and factored combinations |
| `LinearStaticAnalysis`, `ModalAnalysis`, `TimeHistoryAnalysis` | Analysis case definitions |
| `StructuralModel` | Top-level model container |
| `ElementRegistry` | Plugin registry for custom element types |

### `analysis_result` — Analysis Outputs

| Classes | Description |
|:---|:---|
| `NodeDisplacement`, `NodeReaction`, `NodeResult` | Nodal displacements, rotations, and reactions |
| `BeamSectionForce`, `ElementResult` | Internal forces along beam elements |
| `ModeShape`, `ModalResult` | Natural periods and mode shapes |
| `TimeHistoryResult` | Time-series dynamic response |
| `AnalysisResult` | Container keyed by analysis case ID |

### `design_result` — Design Outputs

| Classes | Description |
|:---|:---|
| `CodeCheckResult` | Demand/capacity ratio (DCR) and pass/fail per code clause |
| `FlexureDesignResult`, `ShearDesignResult` | Strength design results |
| `ElementDesignResult` | Composite design summary per member |
| `DesignResult` | Container keyed by element ID |

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
# 50 tests — covers all subpackages and full Project lifecycle JSON round-trip
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
