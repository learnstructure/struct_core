"""
Root StructuralModel container holding nodes, elements, materials, sections, supports, loads, and analysis cases.
"""

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import Field, field_validator, model_validator
from ..base import BaseSchemaModel, ElementId, MaterialId, SectionId
from ..units import Units, parse_units
from .analysis import AnalysisCase
from .elements import Element
from .groups import ObjectGroup
from .loads import AreaLoad, GroundMotion, LoadCase, LoadCombination, MassSource
from .materials import Material
from .migration import migrate_element_materials
from .nodes import Node
from .sections import Section
from .shells import ShellElement, ShellSection
from .supports import Support


class StructuralModel(BaseSchemaModel):
    """
    Main structural model container holding physical, material, boundary condition, and loading data.

    Elements reference sections and sections reference materials; :meth:`section_of` and :meth:`material_of`
    resolve them. Units and project metadata are owned canonically by `Project.metadata`.
    """
    dimension: Optional[Literal["2D", "3D"]] = Field(default=None, description="Spatial dimensionality ('2D' or '3D')")
    vertical_axis: Optional[Literal["Y", "Z"]] = Field(default=None, description="Global vertical / gravity axis ('Y' or 'Z')")
    units: Optional[Units] = Field(default=None, description="Model engineering units when used standalone")
    nodes: List[Node] = Field(default_factory=list, description="List of structural nodes")
    elements: List[Element] = Field(default_factory=list, description="List of structural elements")
    materials: List[Material] = Field(default_factory=list, description="List of material definitions")
    sections: List[Section] = Field(default_factory=list, description="List of cross-section definitions")
    shell_elements: List[ShellElement] = Field(
        default_factory=list, description="Shell (area) elements: slabs and walls, 3 or 4 nodes each"
    )
    shell_sections: List[ShellSection] = Field(default_factory=list, description="Sections of the shell elements")
    supports: List[Support] = Field(default_factory=list, description="List of support boundary conditions")
    load_cases: List[LoadCase] = Field(default_factory=list, description="List of load cases")
    load_combinations: List[LoadCombination] = Field(default_factory=list, description="List of load combinations")
    area_loads: List[AreaLoad] = Field(default_factory=list, description="List of area/surface loads applied over floors/panels")
    story_elevations: List[float] = Field(default_factory=list, description="List of floor/story elevations (Z or Y coordinates)")
    groups: List[ObjectGroup] = Field(default_factory=list, description="Named groups of nodes, elements, and shell elements")
    ground_motions: List[GroundMotion] = Field(default_factory=list, description="List of ground motion records")
    analysis_cases: List[AnalysisCase] = Field(default_factory=list, description="List of analysis cases")
    mass_source: Optional[MassSource] = Field(default=None, description="Active mass source configuration for modal and dynamic analysis")
    mass_sources: List[MassSource] = Field(default_factory=list, description="List of defined mass sources")

    @field_validator("units", mode="before")
    @classmethod
    def _validate_units(cls, val: Any) -> Optional[Units]:
        if val is None or isinstance(val, Units):
            return val
        return parse_units(val)

    def __init__(self, **data: Any):
        meta = data.pop("metadata", None)
        if "units" not in data and isinstance(meta, dict) and "units" in meta:
            data["units"] = meta["units"]
        elif "units" not in data and hasattr(meta, "units") and getattr(meta, "units", None) is not None:
            data["units"] = meta.units
        super().__init__(**data)

    @model_validator(mode="before")
    @classmethod
    def _migrate_element_materials(cls, data: Any) -> Any:
        return migrate_element_materials(data)

    # ── Lookups ──────────────────────────────────────────────────────────────

    def get_material(self, material_id: Optional[MaterialId]) -> Optional[Material]:
        """The material with ID ``material_id``, or None."""
        return next((m for m in self.materials if m.id == material_id), None)

    def get_section(self, section_id: Optional[SectionId]) -> Optional[Section]:
        """The section with ID ``section_id``, or None."""
        return next((s for s in self.sections if s.id == section_id), None)

    def get_shell_section(self, section_id: Optional[SectionId]) -> Optional[ShellSection]:
        """The shell section with ID ``section_id``, or None."""
        return next((s for s in self.shell_sections if s.id == section_id), None)

    def get_shell_element(self, element_id: Optional[ElementId]) -> Optional[ShellElement]:
        """The shell element with ID ``element_id``, or None."""
        return next((e for e in self.shell_elements if e.id == element_id), None)

    def get_group(self, name: str) -> Optional[ObjectGroup]:
        """The object group named ``name``, or None."""
        return next((g for g in self.groups if g.name == name), None)

    def section_of(
        self, element: Union[Element, ShellElement, ElementId]
    ) -> Optional[Union[Section, ShellSection]]:
        """The section of an element or shell element (or of an element ID); None for an element without one (a
        spring) or a missing one. A shell element resolves to a shell section."""
        if not hasattr(element, "id"):
            element = (next((e for e in self.elements if e.id == element), None)
                       or self.get_shell_element(element))
        if isinstance(element, ShellElement):
            return self.get_shell_section(element.section_id)
        return self.get_section(getattr(element, "section_id", None))

    def material_of(self, item: Union[Element, ShellElement, Section, ShellSection, ElementId]) -> Optional[Material]:
        """The material of a section, or of an element through its section; None if there is none."""
        section = item if hasattr(item, "material_id") else self.section_of(item)
        return self.get_material(getattr(section, "material_id", None))
