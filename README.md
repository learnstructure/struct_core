# struct_core

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Pydantic v2](https://img.shields.io/badge/pydantic-v2-green)](https://docs.pydantic.dev/)

A standalone, neutral engineering schema for 2D and 3D structural analysis.

**struct_core** is a Pydantic v2–based Python package that defines the common data language for the structural engineering ecosystem built around [fem2d](https://github.com/learnstructure/fem-2d) and [structdyn](https://github.com/learnstructure/structdyn).

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
               ┌────────┴────────┐
               ▼                 ▼
            fem2d            structdyn
       (FE Assembly)     (Modal / Dynamics)
               │                 │
               └────────┬────────┘
                        ▼
                  Results / Reports
```

Every tool speaks one neutral engineering language. Solvers are free to evolve independently. The schema is the single source of truth.

---

## Features

- **Declarative Domain Models** — Pure data schemas for nodes, elements, materials, sections, supports, loads, and analysis cases. No solver logic, no matrix math.
- **Pydantic v2 Validation** — Strong type checking, referential integrity (missing node/material/section references), duplicate ID detection, and zero-length element checks.
- **JSON Serialization** — Full round-trip JSON and Python dictionary import/export with `to_json()`, `from_json()`, `save_json()`, and `load_json()`.
- **Polymorphic Type System** — Discriminated unions for materials (`elastic`, `bilinear`), sections (`rectangular`, `circular`, `general`), elements (`beam`, `truss`, `spring`), and analysis cases (`linear_static`, `nonlinear_static`, `modal`, `time_history`).
- **Layered Model Structure** — A `Project` container wraps `Metadata` (title, author, units) and `StructuralModel` (geometry, properties, boundary conditions, loading, analysis cases).
- **Lightweight Plugin Registry** — Register custom element types via `@ElementRegistry.register("custom_type")` without modifying core source code.
- **3D Ready** — Nodes carry `(x, y, z)` coordinates with `z=0.0` default, ensuring a clean upgrade path to full 3D support.
- **Solver Adapters** — `fem2d` and `structdyn` ship their own adapter modules that convert `struct_core` models into solver-ready objects. The schema package itself has zero solver dependencies.

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

## Quick Start

### Define a Portal Frame Model

```python
from struct_core import (
    Project,
    StructuralModel,
    Node,
    BeamElement,
    ElasticMaterial,
    RectangularSection,
    Support,
    LoadCase,
    PointLoad,
    DistributedLoad,
    LinearStaticAnalysis,
    validate_structural_model,
    to_json,
)

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
        RectangularSection(id="Col", b=0.30, h=0.30),
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
from struct_core import validate_structural_model

validate_structural_model(model)
# Raises StructuralValidationError clearly describing any issues
# before any solver is called.
```

### Save and Load as JSON

```python
from struct_core import to_json, from_json

json_str = to_json(project, indent=2)
reloaded = from_json(Project, json_str)
```

### Run Analysis with fem2d

```python
from fem2d import from_schema

structure = from_schema(project)
structure.solve()
```

---

## Schema Overview

| Module | Classes |
|:---|:---|
| `metadata` | `Metadata`, `Units` |
| `nodes` | `Node` |
| `materials` | `ElasticMaterial`, `BilinearMaterial` |
| `sections` | `RectangularSection`, `CircularSection`, `GeneralSection` |
| `elements` | `BeamElement`, `TrussElement`, `SpringElement` |
| `supports` | `Support` (with `pinned`, `fixed`, `roller_x`, `roller_y` factory methods) |
| `loads` | `PointLoad`, `DistributedLoad`, `GroundMotion`, `LoadCase`, `LoadCombination` |
| `analysis` | `LinearStaticAnalysis`, `NonlinearStaticAnalysis`, `ModalAnalysis`, `TimeHistoryAnalysis` |
| `model` | `StructuralModel` |
| `project` | `Project` |
| `validation` | `validate_structural_model`, `StructuralValidationError` |
| `serialization` | `to_dict`, `from_dict`, `to_json`, `from_json`, `save_json`, `load_json` |
| `registry` | `ElementRegistry` |

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
| [fem2d](https://github.com/learnstructure/fem-2d) | 2D finite element solver for static and nonlinear analysis |
| [structdyn](https://github.com/learnstructure/structdyn) | Structural dynamics: modal, response spectrum, time history |

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
