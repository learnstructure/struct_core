"""
struct_core: A common engineering schema for 2D/3D structural analysis and structural dynamics.
"""

from .analysis import (
    AnalysisCase,
    AnalysisCaseId,
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
from .base import (
    BaseSchemaModel,
    ElementId,
    IDType,
    LoadCaseId,
    MaterialId,
    NodeId,
    SectionId,
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
from .metadata import Metadata, ModelMetadata, Units, UnitsSchema
from .model import StructuralModel
from .nodes import Node, NodeSchema
from .project import Project
from .registry import ElementRegistry
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
from .serialization import from_dict, from_json, load_json, save_json, to_dict, to_json
from .supports import Support, SupportSchema
from .validation import StructuralValidationError, validate_structural_model

__version__ = "0.1.0"

__all__ = [
    # Metadata & Units
    "Metadata",
    "Units",
    "ModelMetadata",
    "UnitsSchema",
    # Base
    "BaseSchemaModel",
    "IDType",
    "NodeId",
    "ElementId",
    "MaterialId",
    "SectionId",
    "LoadCaseId",
    "AnalysisCaseId",
    # Nodes & Elements
    "Node",
    "NodeSchema",
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
    # Materials & Sections
    "BaseMaterial",
    "BaseMaterialSchema",
    "ElasticMaterial",
    "ElasticMaterialSchema",
    "BilinearMaterial",
    "BilinearMaterialSchema",
    "Material",
    "MaterialSchema",
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
    # Supports & Boundary Conditions
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
    # Analysis Cases
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
    # Models & Project Containers
    "StructuralModel",
    "Project",
    # Validation
    "validate_structural_model",
    "StructuralValidationError",
    # Serialization
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
    "save_json",
    "load_json",
]
