# struct_core.design_result

The canonical, **future-stable** location of the output engineering result
produced by design packages and consumed by reporting / detailing packages.

## Planned families

* `MaterialDesignResult` — required `As`, `Mu/phi`, strength reduction, governing code clause.
* `DetailingResult` — rebar schedule, splice lengths, anchorage lengths, confinement requirements.
* `ElementDesignResult` — composite result per structural element.
* `CodeCheckResult` — capacity / demand ratios, utilisation, pass / fail flags.
* `DesignResult` — top-level container keyed by design code and member.

## Status

🚧 **Scaffolded.** The schema is **planned but not yet implemented**.

Today, design packages (`aci318`, `struct_detail`, ...) define their own
result classes internally (e.g. `aci318.results.FlexuralDesignResult`,
`structdetail.results.ScheduleResult`). Once the schema lands here, design
adapters will be migrated to populate `struct_core.design_result.*` objects
instead.