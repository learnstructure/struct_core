"""
Project schema representing the top-level container combining metadata, structural model, and lifecycle engineering results.
"""

from typing import Any, Dict, Optional
from pydantic import Field
from .analysis_result import AnalysisResult
from .base import BaseSchemaModel
from .design_result import DesignResult
from .detailing_result import DetailingResult
from .metadata import Metadata
from .structural_model import StructuralModel


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
        return next(iter(self.analysis_results.values()))


    @property
    def design_result(self) -> Optional[DesignResult]:
        """Convenience accessor for the primary or first design result."""
        if self.design_results:
            return next(iter(self.design_results.values()))
        return None

    @property
    def detailing_result(self) -> Optional[DetailingResult]:
        """Convenience accessor for the primary or first detailing result."""
        if self.detailing_results:
            return next(iter(self.detailing_results.values()))
        return None

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


