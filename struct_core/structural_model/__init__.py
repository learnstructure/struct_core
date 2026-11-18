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
    ResponseSpectrumAnalysis,
)
from .elements import (
    STIFFNESS_MODIFIER_KEYS,
    BaseElement,
    BeamElement,
    Element,
    SpringElement,
    TrussElement,
)
from .loads import (
    AreaLoad,
    DistributedLoad,
    ElementPointLoad,
    GroundMotion,
    LoadCase,
    LoadCaseFactor,
    LoadCombination,
    MassSource,
    MassSourceFactor,
    PointLoad,
    VALID_LOAD_TYPES,
    classify_load_case,
)
from .materials import (
    BaseMaterial,
    BilinearMaterial,
    ConcreteMaterial,
    ElasticMaterial,
    Material,
    RebarMaterial,
)
from .model import StructuralModel
from .nodes import Node
from .sections import (
    BaseSection,
    CircularSection,
    GeneralSection,
    RectangularSection,
    Section,
    SolidSection,
)
from .registry import ElementRegistry
from .supports import Support
from .topology import (
    FrameStory,
    classify_frame_members,
    frame_levels,
    frame_stories,
    node_elevation,
    vertical_axis,
)
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
    "ConcreteMaterial",
    "RebarMaterial",
    "BilinearMaterial",
    "Material",
    # Sections
    "BaseSection",
    "SolidSection",
    "RectangularSection",
    "CircularSection",
    "GeneralSection",
    "Section",
    # Elements
    "BaseElement",
    "TrussElement",
    "BeamElement",
    "STIFFNESS_MODIFIER_KEYS",
    "SpringElement",
    "Element",
    "ElementRegistry",
    # Supports
    "Support",
    # Loads
    "AreaLoad",
    "PointLoad",
    "ElementPointLoad",
    "VALID_LOAD_TYPES",
    "classify_load_case",
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
    "ResponseSpectrumAnalysis",
    "AnalysisCase",
    # Containers
    "StructuralModel",
    # Topology
    "FrameStory",
    "classify_frame_members",
    "frame_levels",
    "frame_stories",
    "node_elevation",
    "vertical_axis",
    # Validation
    "validate_structural_model",
    "StructuralValidationError",
]