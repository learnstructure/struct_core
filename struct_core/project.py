"""
Project schema representing the top-level container combining metadata, structural model, and lifecycle engineering results.
"""

from typing import Dict, Optional
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

    @property
    def analysis_result(self) -> Optional[AnalysisResult]:
        """Convenience accessor for the primary or first analysis result."""
        if self.analysis_results:
            return next(iter(self.analysis_results.values()))
        return None

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
