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
    AnalysisCaseSchema,
    BaseAnalysisCase,
    BaseAnalysisCaseSchema,
    LinearStaticAnalysis,
    LinearStaticAnalysisSchema,
    ModalAnalysis,
    ModalAnalysisSchema,
    NonlinearStaticAnalysis,
    NonlinearStaticAnalysisSchema,
    TimeHistoryAnalysis,
    TimeHistoryAnalysisSchema,
)
from .elements import (
    BaseElement,
    BaseElementSchema,
    BeamElement,
    BeamElementSchema,
    Element,
    ElementSchema,
    SpringElement,
    SpringElementSchema,
    TrussElement,
    TrussElementSchema,
)
from .loads import (
    DistributedLoad,
    DistributedLoadSchema,
    GroundMotion,
    GroundMotionSchema,
    LoadCase,
    LoadCaseFactor,
    LoadCaseFactorSchema,
    LoadCaseSchema,
    LoadCombination,
    LoadCombinationSchema,
    PointLoad,
    PointLoadSchema,
)
from .materials import (
    BaseMaterial,
    BaseMaterialSchema,
    BilinearMaterial,
    BilinearMaterialSchema,
    ElasticMaterial,
    ElasticMaterialSchema,
    Material,
    MaterialSchema,
)
from .model import StructuralModel
from .nodes import Node, NodeSchema
from .sections import (
    BaseSection,
    BaseSectionSchema,
    CircularSection,
    CircularSectionSchema,
    GeneralSection,
    GeneralSectionSchema,
    RectangularSection,
    RectangularSectionSchema,
    Section,
    SectionSchema,
)
from .registry import ElementRegistry
from .supports import Support, SupportSchema
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
    "NodeSchema",
    # Materials
    "BaseMaterial",
    "BaseMaterialSchema",
    "ElasticMaterial",
    "ElasticMaterialSchema",
    "BilinearMaterial",
    "BilinearMaterialSchema",
    "Material",
    "MaterialSchema",
    # Sections
    "BaseSection",
    "BaseSectionSchema",
    "RectangularSection",
    "RectangularSectionSchema",
    "CircularSection",
    "CircularSectionSchema",
    "GeneralSection",
    "GeneralSectionSchema",
    "Section",
    "SectionSchema",
    # Elements
    "BaseElement",
    "BaseElementSchema",
    "TrussElement",
    "TrussElementSchema",
    "BeamElement",
    "BeamElementSchema",
    "SpringElement",
    "SpringElementSchema",
    "Element",
    "ElementSchema",
    "ElementRegistry",
    # Supports
    "Support",
    "SupportSchema",
    # Loads
    "PointLoad",
    "PointLoadSchema",
    "DistributedLoad",
    "DistributedLoadSchema",
    "GroundMotion",
    "GroundMotionSchema",
    "LoadCase",
    "LoadCaseSchema",
    "LoadCaseFactor",
    "LoadCaseFactorSchema",
    "LoadCombination",
    "LoadCombinationSchema",
    # Analysis cases
    "BaseAnalysisCase",
    "BaseAnalysisCaseSchema",
    "LinearStaticAnalysis",
    "LinearStaticAnalysisSchema",
    "NonlinearStaticAnalysis",
    "NonlinearStaticAnalysisSchema",
    "ModalAnalysis",
    "ModalAnalysisSchema",
    "TimeHistoryAnalysis",
    "TimeHistoryAnalysisSchema",
    "AnalysisCase",
    "AnalysisCaseSchema",
    # Containers
    "StructuralModel",
    # Validation
    "validate_structural_model",
    "StructuralValidationError",
]