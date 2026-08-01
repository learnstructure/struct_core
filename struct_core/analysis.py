"""
Analysis case schemas for linear static, nonlinear static, modal, and dynamic time-history analysis.
"""

from typing import Annotated, Literal, Optional, Union
from pydantic import Field
from .base import AnalysisCaseId, BaseSchemaModel, LoadCaseId


class BaseAnalysisCase(BaseSchemaModel):
    """
    Base class for analysis case definitions.
    """
    id: AnalysisCaseId = Field(description="Unique analysis case identifier")
    name: Optional[str] = Field(default=None, description="Human-readable analysis case name")


class LinearStaticAnalysis(BaseAnalysisCase):
    """
    Linear static analysis configuration.
    """
    type: Literal["linear_static"] = "linear_static"
    load_case_id: Optional[LoadCaseId] = Field(default=None, description="Target load case ID to solve")
    load_combination_id: Optional[str] = Field(default=None, description="Target load combination ID to solve")


class NonlinearStaticAnalysis(BaseAnalysisCase):
    """
    Nonlinear static analysis configuration (geometric and/or material nonlinearity).
    """
    type: Literal["nonlinear_static"] = "nonlinear_static"
    load_case_id: Optional[LoadCaseId] = Field(default=None, description="Target load case ID")
    load_combination_id: Optional[str] = Field(default=None, description="Target load combination ID")
    max_steps: int = Field(default=10, gt=0, description="Number of load increments/steps")
    max_iter: int = Field(default=50, gt=0, description="Maximum Newton-Raphson iterations per step")
    tolerance: float = Field(default=1e-4, gt=0.0, description="Convergence tolerance threshold")


class ModalAnalysis(BaseAnalysisCase):
    """
    Modal eigenvalue analysis configuration.
    """
    type: Literal["modal"] = "modal"
    num_modes: int = Field(default=3, gt=0, description="Number of natural modes to compute")


class TimeHistoryAnalysis(BaseAnalysisCase):
    """
    Dynamic time history integration analysis configuration.
    """
    type: Literal["time_history"] = "time_history"
    ground_motion_id: str = Field(description="Target ground motion ID")
    dt: float = Field(default=0.01, gt=0.0, description="Integration time step increment (seconds)")
    total_time: float = Field(gt=0.0, description="Total duration of dynamic time history analysis")
    damping_ratio: float = Field(default=0.05, ge=0.0, le=1.0, description="Viscous damping ratio (e.g., 0.05 for 5%)")


# Discriminated union for polymorphic analysis case deserialization
AnalysisCase = Annotated[
    Union[
        LinearStaticAnalysis,
        NonlinearStaticAnalysis,
        ModalAnalysis,
        TimeHistoryAnalysis,
    ],
    Field(discriminator="type")
]

# Backward-compatible aliases
BaseAnalysisCaseSchema = BaseAnalysisCase
LinearStaticAnalysisSchema = LinearStaticAnalysis
NonlinearStaticAnalysisSchema = NonlinearStaticAnalysis
ModalAnalysisSchema = ModalAnalysis
TimeHistoryAnalysisSchema = TimeHistoryAnalysis
AnalysisCaseSchema = AnalysisCase
