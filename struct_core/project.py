"""
Project schema representing the top-level container combining metadata, structural model, and lifecycle engineering results.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import Field, model_validator
from .analysis_result import AnalysisResult
from .base import BaseSchemaModel
from .design_basis import SeismicDesignBasis
from .design_result import AppliedDefault, DesignResult
from .detailing_result import DetailingResult
from .metadata import Metadata
from .structural_model import StructuralModel
from .units import Units, parse_units


class Project(BaseSchemaModel):
    """
    Top-level project aggregate wrapping metadata header, structural model input data,
    and accumulated lifecycle engineering outputs (analysis, design, detailing results).
    """
    metadata: Metadata = Field(default_factory=Metadata, description="Project metadata and engineering units")
    model: StructuralModel = Field(default_factory=StructuralModel, description="Structural model input container")
    analysis_results: Dict[str, AnalysisResult] = Field(
        default_factory=dict, description="Analysis results produced by solvers (fem2d, structdyn, etc.) keyed by analysis case ID"
    )
    design_results: Dict[str, DesignResult] = Field(
        default_factory=dict, description="Design results produced by code design engines (aci318, etc.) keyed by design case ID"
    )
    detailing_results: Dict[str, DetailingResult] = Field(
        default_factory=dict, description="Detailing results produced by detailing engines (aci318, etc.) keyed by detailing case ID"
    )

    active_analysis_case: Optional[str] = Field(
        default=None, description="Currently selected or active analysis case ID for display/design"
    )
    seismic_basis: Optional[SeismicDesignBasis] = Field(
        default=None,
        description="Seismic design basis (system, R, Omega0, Cd, Ie, ...) recorded when seismic loads are applied",
    )
    defaults_applied: List[AppliedDefault] = Field(
        default_factory=list,
        description="Engineering defaults applied to this project during modeling and design",
    )

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_data(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data = dict(data)
            # Check legacy units conflict
            meta = data.get("metadata")
            mod = data.get("model")
            proj_u = None
            mod_u = None
            if isinstance(meta, dict):
                proj_u = meta.get("units")
            elif isinstance(meta, Metadata):
                proj_u = meta.units

            if isinstance(mod, dict):
                if "metadata" in mod and isinstance(mod["metadata"], dict):
                    mod_u = mod["metadata"].get("units")
                if mod_u is None and "units" in mod:
                    mod_u = mod.get("units")
            elif isinstance(mod, StructuralModel):
                mod_u = mod.units

            if proj_u is not None and mod_u is not None:
                p_parsed = parse_units(proj_u) if isinstance(proj_u, (str, dict)) else proj_u
                m_parsed = parse_units(mod_u) if isinstance(mod_u, (str, dict)) else mod_u
                if p_parsed != m_parsed:
                    p_lbl = getattr(p_parsed, "short_label", str(p_parsed))
                    m_lbl = getattr(m_parsed, "short_label", str(m_parsed))
                    raise ValueError(f"Project units '{p_lbl}' differ from model units '{m_lbl}'")

            if "metadata" not in data and "model" in data and isinstance(data["model"], dict):
                model_dict = data["model"]
                if "metadata" in model_dict:
                    meta = model_dict.get("metadata")
                    if isinstance(meta, dict):
                        raw_elems = model_dict.get("elements") or []
                        if any(isinstance(e, dict) and "material_id" in e for e in raw_elems):
                            meta = {k: v for k, v in meta.items() if k != "schema_version"}
                    data["metadata"] = meta
                elif "units" in model_dict:
                    data["metadata"] = {"units": model_dict["units"]}
            elif "metadata" in data and isinstance(data["metadata"], dict) and "units" not in data["metadata"]:
                if "model" in data and isinstance(data["model"], dict) and "units" in data["model"]:
                    data["metadata"]["units"] = data["model"]["units"]
        return data

    @model_validator(mode="after")
    def _sync_and_validate_units(self) -> "Project":
        if self.metadata is not None:
            object.__setattr__(self.metadata, "_project", self)
        if self.model is None:
            return self
        proj_units = self.metadata.units if self.metadata else None
        model_units = self.model.units
        if model_units is None:
            if proj_units is not None:
                self.model.units = proj_units
        elif proj_units is None or "units" not in self.metadata.model_fields_set:
            self.metadata.units = model_units
        else:
            if proj_units != model_units:
                raise ValueError(
                    f"Project units '{proj_units}' differ from model units '{model_units}'; "
                    f"convert with convert_project_units() or give matching units"
                )
        return self

    def __init__(self, **data: Any):
        if "units" in data:
            units = data.pop("units")
            u_parsed = parse_units(units) if isinstance(units, (str, dict)) else units
            if "metadata" not in data:
                data["metadata"] = Metadata(units=u_parsed)
            elif isinstance(data["metadata"], dict):
                data["metadata"]["units"] = u_parsed
            elif isinstance(data["metadata"], Metadata):
                data["metadata"].units = u_parsed
        super().__init__(**data)

    @property
    def analysis_result(self) -> Optional[AnalysisResult]:
        """Convenience accessor for the active, governing, or primary analysis result."""
        if not self.analysis_results:
            return None
        if self.active_analysis_case and self.active_analysis_case in self.analysis_results:
            return self.analysis_results[self.active_analysis_case]
        for key in ("envelope", "Envelope", "total", "Total", "LCASE1", "DEAD"):
            if key in self.analysis_results:
                return self.analysis_results[key]
        return list(self.analysis_results.values())[-1]

    @property
    def design_result(self) -> Optional[DesignResult]:
        """Convenience accessor for the latest or active design result."""
        if self.design_results:
            return list(self.design_results.values())[-1]
        return None

    @property
    def detailing_result(self) -> Optional[DetailingResult]:
        """Convenience accessor for the latest or active detailing result."""
        if self.detailing_results:
            return list(self.detailing_results.values())[-1]
        return None

    @property
    def units(self) -> Units:
        """The single canonical unit authority for this project."""
        return self.metadata.units

    @units.setter
    def units(self, val: Union[Units, str, Dict[str, Any]]):
        u = parse_units(val) if isinstance(val, (str, dict)) else val
        if not isinstance(u, Units):
            raise TypeError(f"Expected Units, str, or dict, got {type(val).__name__}")
        self.metadata.units = u
        if hasattr(self, "model") and self.model is not None:
            self.model.units = u

    def convert_units(self, to_units: Union[Units, str, Dict[str, Any]]) -> "Project":
        """Convert all project numerical quantities to the target units system."""
        from .units import convert_project_units
        return convert_project_units(self, to_units, in_place=True)

    def __getattr__(self, name: str) -> Any:
        # Delegate structural model attributes and methods to self.model
        if name != "model" and hasattr(self, "model") and hasattr(self.model, name):
            return getattr(self.model, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in (
            "nodes", "elements", "materials", "sections", "supports",
            "shell_elements", "shell_sections", "groups",
            "load_cases", "load_combinations", "area_loads", "story_elevations",
            "ground_motions", "analysis_cases", "mass_source", "mass_sources",
            "dimension", "vertical_axis",
        ):
            if hasattr(self, "model") and self.model is not None:
                setattr(self.model, name, value)
                return
        super().__setattr__(name, value)

    def save_json(self, path: str) -> None:
        """Save Project to a formatted JSON file."""
        from pathlib import Path
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load_json(cls, path: str) -> "Project":
        """Load Project from a JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            return cls.model_validate_json(f.read())

    def convert_units(self, to_units: Any, in_place: bool = True) -> "Project":
        """
        Convert the entire project, model geometry, materials, sections, loads,
        and analysis results to the specified target unit system.
        """
        from .units import convert_project_units
        return convert_project_units(self, to_units, in_place=in_place)


