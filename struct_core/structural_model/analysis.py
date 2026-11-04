"""
Analysis case schemas for linear static, nonlinear static, modal, and dynamic time-history analysis.
"""

from typing import Annotated, Literal, Optional, Union
from pydantic import Field
from ..base import AnalysisCaseId, BaseSchemaModel, LoadCaseId


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


class ResponseSpectrumAnalysis(BaseAnalysisCase):
    """
    Dynamic response spectrum analysis configuration.
    """
    type: Literal["response_spectrum"] = "response_spectrum"
    direction: str = Field(default="X", description="Excitation direction ('X', 'Y', or 'Z')")
    combination: str = Field(default="CQC", description="Modal combination rule ('CQC', 'SRSS', 'ABS')")
    damping_ratio: float = Field(default=0.05, ge=0.0, le=1.0, description="Modal damping ratio")
    scale_factor: Optional[float] = Field(default=None, gt=0.0, description="Acceleration scale factor")
    function_name: Optional[str] = Field(default=None, description="Response spectrum function name")
    sds: Optional[float] = Field(default=None, description="ASCE 7 short-period spectral acceleration SDS (g)")
    sd1: Optional[float] = Field(default=None, description="ASCE 7 1-second spectral acceleration SD1 (g)")
    tl: Optional[float] = Field(default=None, description="Long-period transition period TL (s)")
    site_class: Optional[str] = Field(default=None, description="Site class (A, B, C, D, E, F)")


# Discriminated union for polymorphic analysis case deserialization
AnalysisCase = Annotated[
    Union[
        LinearStaticAnalysis,
        NonlinearStaticAnalysis,
        ModalAnalysis,
        TimeHistoryAnalysis,
        ResponseSpectrumAnalysis,
    ],
    Field(discriminator="type")
]


