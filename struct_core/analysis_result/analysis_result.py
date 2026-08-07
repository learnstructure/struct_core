"""
Top-level composite AnalysisResult schema holding nodal, element, modal, and dynamic time history outputs.
"""

from typing import Dict, Optional
from pydantic import Field
from ..base import AnalysisCaseId, BaseSchemaModel, ElementId, NodeId
from .element_result import ElementResult
from .modal_result import ModalResult
from .node_result import NodeResult
from .time_history_result import TimeHistoryResult


class AnalysisResult(BaseSchemaModel):
    """
    Top-level analysis result container associated with an analysis case.
    Stores nodal displacements/reactions, element forces, modal results, and time history responses.
    """
    analysis_case_id: AnalysisCaseId = Field(description="Associated analysis case identifier")
    node_results: Dict[NodeId, NodeResult] = Field(default_factory=dict, description="Nodal output results keyed by NodeId")
    element_results: Dict[ElementId, ElementResult] = Field(default_factory=dict, description="Element output results keyed by ElementId")
    modal_result: Optional[ModalResult] = Field(default=None, description="Modal eigenvalue analysis results (if applicable)")
    time_history_result: Optional[TimeHistoryResult] = Field(default=None, description="Dynamic time history analysis results (if applicable)")
