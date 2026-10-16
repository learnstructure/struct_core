"""
struct_core.structural_model
============================

The input engineering model consumed by solvers and design packages.
"""

from ..base import (
    AnalysisCaseId,
    BaseSchemaModel,
    ElementId,
    IDType,
    LoadCaseId,
    MaterialId,
    NodeId,
    SectionId,
)
from .analysis import (
    AnalysisCase,
    BaseAnalysisCase,
    LinearStaticAnalysis,
    ModalAnalysis,
    NonlinearStaticAnalysis,
    TimeHistoryAnalysis,
)
from .elements import (
    BaseElement,
    BeamElement,
    Element,
    SpringElement,
    TrussElement,
)
from .loads import (
    AreaLoad,
    DistributedLoad,
    GroundMotion,
    LoadCase,
    LoadCaseFactor,
    LoadCombination,
    MassSource,
    MassSourceFactor,
    PointLoad,
)
from .materials import (
    BaseMaterial,
    BilinearMaterial,
    ElasticMaterial,
    Material,
)
from .model import StructuralModel
from .nodes import Node
from .sections import (
    BaseSection,
    CircularSection,
    GeneralSection,
    RectangularSection,
    Section,
)
from .registry import ElementRegistry
from .supports import Support
from .validation import StructuralValidationError, validate_structural_model

__all__ = [
    # Base / IDs
    "BaseSchemaModel",
    "IDType",
    "NodeId",
    "ElementId",
    "MaterialId",
    "SectionId",
    "LoadCaseId",
    "AnalysisCaseId",
    # Nodes
    "Node",
    # Materials
    "BaseMaterial",
    "ElasticMaterial",
    "BilinearMaterial",
    "Material",
    # Sections
    "BaseSection",
    "RectangularSection",
    "CircularSection",
    "GeneralSection",
    "Section",
    # Elements
    "BaseElement",
    "TrussElement",
    "BeamElement",
    "SpringElement",
    "Element",
    "ElementRegistry",
    # Supports
    "Support",
    # Loads
    "AreaLoad",
    "PointLoad",
    "DistributedLoad",
    "GroundMotion",
    "LoadCase",
    "LoadCaseFactor",
    "LoadCombination",
    "MassSource",
    "MassSourceFactor",
    # Analysis cases
    "BaseAnalysisCase",
    "LinearStaticAnalysis",
    "NonlinearStaticAnalysis",
    "ModalAnalysis",
    "TimeHistoryAnalysis",
    "AnalysisCase",
    # Containers
    "StructuralModel",
    # Validation
    "validate_structural_model",
    "StructuralValidationError",
]