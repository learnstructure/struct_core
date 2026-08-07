# struct_core.analysis_result

The canonical, **future-stable** location of the output engineering result
produced by solver packages and consumed by downstream design packages.

## Planned families

* `NodeResult` — displacements / rotations / reactions at a node.
* `ElementResult` — internal forces per element (axial, shear, moment).
* `ModalResult` — natural periods, mode shapes, participating mass.
* `TimeHistoryResult` — time-series displacements / accelerations.
* `LinearStaticResult`, `NonlinearStaticResult` — composite results.
* `AnalysisResult` — top-level container keyed by analysis case.

## Status

🚧 **Scaffolded.** The schema is **planned but not yet implemented**.

Today, solver packages (`fem2d`, `structdyn`, ...) define their own
result classes internally. Once the schema lands here, solver adapters
will be migrated to populate `struct_core.analysis_result.*` objects
instead of bespoke result classes.