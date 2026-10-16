"""
struct_core
===========

Single source of truth for schemas, data structures, and utilities across
the entire structural engineering ecosystem.
"""

from . import analysis_result, design_result, detailing_result, structural_model
from .analysis_result import (
    AnalysisResult,
    BeamSectionForce,
    ElementForceResult,
    ElementResult,
    ModalResult,
    ModeShape,
    NodeDisplacement,
    NodeReaction,
    NodeResult,
    TimeHistoryResult,
    TimeStepResult,
)
from .base import (
    AnalysisCaseId,
    BaseSchemaModel,
    ElementId,
    IDType,
    LoadCaseId,
    MaterialId,
    NodeId,
    SectionId,
)
from .design_result import (
    CodeCheckResult,
    DesignResult,
    ElementDesignResult,
    FlexureDesignResult,
    MaterialDesignResult,
    ShearDesignResult,
)
from .detailing_result import (
    Anchorage,
    Bar,
    BarLayout,
    BarSchedule,
    BarScheduleItem,
    DetailingResult,
    ElementDetailingResult,
    HookGeometry,
    LapSplice,
    RebarLayer,
    StirrupLayout,
)
from .metadata import Metadata, Units
from .units import (
    PRESETS,
    DIMENSIONS,
    UnitLabels,
    conversion_factor,
    convert_project_units,
    get_unit_labels,
    normalize_unit_str,
    parse_units,
)
from .project import Project
from .serialization import from_dict, from_json, load_json, save_json, to_dict, to_json
from .structural_model import (
    AnalysisCase,
    AreaLoad,
    BaseAnalysisCase,
    BaseElement,
    BaseMaterial,
    BaseSection,
    BeamElement,
    BilinearMaterial,
    CircularSection,
    DistributedLoad,
    ElasticMaterial,
    Element,
    GeneralSection,
    GroundMotion,
    LinearStaticAnalysis,
    LoadCase,
    LoadCaseFactor,
    LoadCombination,
    MassSource,
    MassSourceFactor,
    Material,
    ModalAnalysis,
    Node,
    NonlinearStaticAnalysis,
    PointLoad,
    RectangularSection,
    Section,
    SpringElement,
    StructuralModel,
    StructuralValidationError,
    Support,
    TimeHistoryAnalysis,
    TrussElement,
    validate_structural_model,
)
from .structural_model.registry import ElementRegistry

# Plural aliases matching ecosystem naming conventions
analysis_results = analysis_result
design_results = design_result
detailing_results = detailing_result

__version__ = "0.2.0"

__all__ = [
    # Subpackages
    "structural_model",
    "analysis_result",
    "design_result",
    "detailing_result",
    "analysis_results",
    "design_results",
    "detailing_results",
    # Metadata & Units
    "Metadata",
    "Units",
    "PRESETS",
    "parse_units",
    "conversion_factor",
    "convert_project_units",
    "get_unit_labels",
    "UnitLabels",
    # Base / IDs
    "BaseSchemaModel",
    "IDType",
    "NodeId",
    "ElementId",
    "MaterialId",
    "SectionId",
    "LoadCaseId",
    "AnalysisCaseId",
    # Structural Model Entities
    "Node",
    "BaseElement",
    "TrussElement",
    "BeamElement",
    "SpringElement",
    "Element",
    "ElementRegistry",
    "BaseMaterial",
    "ElasticMaterial",
    "BilinearMaterial",
    "Material",
    "BaseSection",
    "RectangularSection",
    "CircularSection",
    "GeneralSection",
    "Section",
    "Support",
    "AreaLoad",
    "PointLoad",
    "DistributedLoad",
    "GroundMotion",
    "LoadCase",
    "LoadCaseFactor",
    "LoadCombination",
    "MassSource",
    "MassSourceFactor",
    "BaseAnalysisCase",
    "LinearStaticAnalysis",
    "NonlinearStaticAnalysis",
    "ModalAnalysis",
    "TimeHistoryAnalysis",
    "AnalysisCase",
    "StructuralModel",
    "validate_structural_model",
    "StructuralValidationError",
    # Analysis Results
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
    # Design Results
    "CodeCheckResult",
    "FlexureDesignResult",
    "ShearDesignResult",
    "MaterialDesignResult",
    "ElementDesignResult",
    "DesignResult",
    # Detailing Results
    "Bar",
    "RebarLayer",
    "StirrupLayout",
    "BarLayout",
    "HookGeometry",
    "LapSplice",
    "Anchorage",
    "BarScheduleItem",
    "BarSchedule",
    "ElementDetailingResult",
    "DetailingResult",
    # Project & Utilities
    "Project",
    "to_dict",
    "from_dict",
    "to_json",
    "from_json",
    "save_json",
    "load_json",
]
