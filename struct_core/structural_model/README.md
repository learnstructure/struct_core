# struct_core.structural_model

The **input engineering model** subpackage — the canonical definition of *what the structure is*.

## Modules

| Module | Contents |
|:---|:---|
| `nodes.py` | `Node`, `NodeSchema` |
| `materials.py` | `BaseMaterial`, `ElasticMaterial`, `ConcreteMaterial`, `RebarMaterial`, `BilinearMaterial`, `Material` (discriminated union) |
| `sections.py` | `BaseSection` (with `material_id`), `SolidSection` (reinforcement and cover), `RectangularSection`, `CircularSection`, `GeneralSection`, `Section` (discriminated union) |
| `elements.py` | `BaseElement`, `TrussElement`, `BeamElement`, `SpringElement`, `Element` (discriminated union) |
| `groups.py` | `ObjectGroup` (named node, element, and shell-element groups) |
| `supports.py` | `Support` (with `pinned`, `fixed`, `roller_x`, `roller_y` class-method factories) |
| `loads.py` | `PointLoad`, `DistributedLoad`, `GroundMotion`, `LoadCase`, `LoadCaseFactor`, `LoadCombination` |
| `analysis.py` | `BaseAnalysisCase`, `LinearStaticAnalysis`, `NonlinearStaticAnalysis`, `ModalAnalysis`, `TimeHistoryAnalysis`, `AnalysisCase` (discriminated union) |
| `model.py` | `StructuralModel` (aggregate container for all the above; `section_of`, `material_of`) |
| `migration.py` | `migrate_element_materials`: loads models saved with `material_id` on elements |
| `validation.py` | `validate_structural_model`, `StructuralValidationError` |
| `registry.py` | `ElementRegistry` (singleton plugin registry for custom element types) |

## Importing

Always import from this subpackage directly — **not** from the flat root modules (those are removed):

```python
from struct_core.structural_model import (
    StructuralModel,
    Node, BeamElement,
    ElasticMaterial, RectangularSection,
    Support, LoadCase, PointLoad,
    LinearStaticAnalysis,
    validate_structural_model,
)
```

Or via the top-level shorthand (re-exported from `struct_core/__init__.py`):

```python
from struct_core import Node, BeamElement, StructuralModel  # also works
```

## Status

✅ **Fully implemented** — all schema classes live here. No flat fallback modules remain.