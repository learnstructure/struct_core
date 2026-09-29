"""
struct_core.analysis_result
===========================

The output engineering result produced by solver packages (`fem2d`, `structdyn`, ...).
"""

from .analysis_result import AnalysisResult
from .element_result import BeamSectionForce, ElementForceResult, ElementResult
from .modal_result import ModalResult, ModeShape
from .node_result import NodeDisplacement, NodeReaction, NodeResult
from .superposition import envelope_results, superpose_results
from .time_history_result import TimeHistoryResult, TimeStepResult

__all__ = [
    "NodeDisplacement",
    "NodeReaction",
    "NodeResult",
    "BeamSectionForce",
    "ElementForceResult",
    "ElementResult",
    "ModeShape",
    "ModalResult",
    "TimeStepResult",
    "TimeHistoryResult",
    "AnalysisResult",
    "superpose_results",
    "envelope_results",
]