"""
Load schemas for point loads, distributed loads, ground motions, load cases, and load combinations.
"""

from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from pydantic import Field, field_validator, model_validator
from ..base import BaseSchemaModel, ElementId, LoadCaseId, NodeId


VALID_LOAD_TYPES: Tuple[str, ...] = (
    "dead",
    "super_dead",
    "live",
    "storage_live",
    "roof_live",
    "snow",
    "wind",
    "seismic",
    "partition",
    "soil",
    "fluid",
    "temperature",
)

LOAD_TYPE_SYNONYMS: Dict[str, str] = {
    "self_weight": "dead",
    "dead": "dead",
    "d": "dead",
    "gravity": "dead",
    "g": "dead",
    "super_dead": "super_dead",
    "superimposed_dead": "super_dead",
    "sdl": "super_dead",
    "live": "live",
    "l": "live",
    "ll": "live",
    "occupancy": "live",
    "storage_live": "storage_live",
    "storage": "storage_live",
    "roof_live": "roof_live",
    "roof": "roof_live",
    "roof_ll": "roof_live",
    "lr": "roof_live",
    "snow": "snow",
    "s": "snow",
    "wind": "wind",
    "w": "wind",
    "seismic": "seismic",
    "earthquake": "seismic",
    "eq": "seismic",
    "elf": "seismic",
    "rsa": "seismic",
    "e": "seismic",
    "partition": "partition",
    "soil": "soil",
    "h": "soil",
    "fluid": "fluid",
    "f": "fluid",
    "temperature": "temperature",
    "t": "temperature",
}


def classify_load_case(lc: Any, allow_unknown: bool = False) -> str:
    """
    Classify a load case into its canonical load type:
    'dead', 'super_dead', 'live', 'storage_live', 'roof_live', 'snow', 'wind', 'seismic', 'partition'.

    Parameters
    ----------
    lc : LoadCase or object with id, name, and optional load_type
        The load case to classify.
    allow_unknown : bool, optional
        If True, returns 'unknown' when classification cannot be determined.
        If False (default), raises ValueError.

    Returns
    -------
    str
        Canonical load type string.
    """
    l_type = getattr(lc, "load_type", None)
    if l_type:
        val_str = str(l_type).strip().lower().replace(" ", "_").replace("-", "_")
        canon = LOAD_TYPE_SYNONYMS.get(val_str, val_str)
        if canon in VALID_LOAD_TYPES:
            return canon

    cid = str(getattr(lc, "id", "") or "")
    cname = str(getattr(lc, "name", "") or "")
    cid_lower = cid.lower().strip()
    cname_lower = cname.lower().strip()

    # Match ID and name against canonical patterns (avoiding substring collisions like 'Equipment' -> 'eq')
    # 1. Partition
    if "partition" in cid_lower or "partition" in cname_lower:
        return "partition"

    # 2. Dead & SuperDead & Gravity
    if any(k in cid_lower for k in ("super_dead", "sdl", "superimposed")):
        return "super_dead"
    if any(k in cid_lower for k in ("dead", "self_weight", "selfweight", "sw")):
        return "dead"
    if cid_lower in ("d", "g", "gravity") or cname_lower in ("dead", "gravity"):
        return "dead"
    if "gravity" in cid_lower or "gravity" in cname_lower:
        return "dead"

    # 3. Roof Live
    if any(k in cid_lower for k in ("roof_live", "roof live", "roof_ll")) or cid_lower in ("lr", "rl"):
        return "roof_live"
    if "roof" in cid_lower and "live" in cid_lower:
        return "roof_live"
    if "roof" in cid_lower and "load" in cid_lower:
        return "roof_live"

    # 4. Storage Live
    if "storage" in cid_lower or "storage" in cname_lower:
        return "storage_live"

    # 5. Live
    if any(k in cid_lower for k in ("live", "occupancy", "floor_live")) or cid_lower in ("l", "ll"):
        return "live"

    # 6. Snow
    if "snow" in cid_lower or "snow" in cname_lower or cid_lower in ("s", "sn"):
        return "snow"

    # 7. Wind
    if "wind" in cid_lower or "wind" in cname_lower:
        return "wind"
    if cid_lower in ("w", "wx", "wy", "wz") or cid_lower.startswith(("wind_", "wind-", "w_", "w-")):
        return "wind"

    # 8. Seismic (strictly matches seismic prefixes/keywords, not arbitrary words starting with eq like 'Equipment')
    if any(k in cid_lower for k in ("seismic", "earthquake", "quake", "elf", "rsa")):
        return "seismic"
    if cid_lower in ("eq", "eqx", "eqy", "eqz", "e", "ex", "ey", "ez"):
        return "seismic"
    if cid_lower.startswith(("eq_", "eq-", "seis_", "seis-", "e_")):
        return "seismic"

    if allow_unknown:
        return "unknown"

    raise ValueError(
        f"Unable to determine load type for load case id={cid!r} (name={cname!r}). "
        f"Please explicitly set `load_type` to one of: {sorted(VALID_LOAD_TYPES)}."
    )


class PointLoad(BaseSchemaModel):
    """
    Concentrated force/moment applied to a node [Fx, Fy, Fz, Mx, My, Mz].
    """
    node_id: NodeId = Field(description="Target node ID")
    fx: float = Field(default=0.0, description="Force along X-axis")
    fy: float = Field(default=0.0, description="Force along Y-axis")
    fz: float = Field(default=0.0, description="Force along Z-axis")
    mx: float = Field(default=0.0, description="Moment about X-axis")
    my: float = Field(default=0.0, description="Moment about Y-axis")
    mz: float = Field(default=0.0, description="Moment about Z-axis")


class DistributedLoad(BaseSchemaModel):
    """
    Distributed load applied along an element.
    - Global coordinates (is_local=False): wx, wy, wz along global X, Y, Z (start) and wx_end, wy_end, wz_end (end).
    - Local coordinates (is_local=True): w1, w2, w3 along local axes 1, 2, 3 (start) and w1_end, w2_end, w3_end (end).
    - Relative span: start and end in [0.0, 1.0], with start < end.
    """
    element_id: ElementId = Field(description="Target element ID")
    # Global load components (start intensity)
    wx: float = Field(default=0.0, description="Start intensity along global X-axis")
    wy: float = Field(default=0.0, description="Start intensity along global Y-axis")
    wz: float = Field(default=0.0, description="Start intensity along global Z-axis")
    # Global load components (end intensity, None means uniform equal to start)
    wx_end: Optional[float] = Field(default=None, description="End intensity along global X-axis")
    wy_end: Optional[float] = Field(default=None, description="End intensity along global Y-axis")
    wz_end: Optional[float] = Field(default=None, description="End intensity along global Z-axis")
    # Local load components (start intensity)
    w1: float = Field(default=0.0, description="Start intensity along local 1-axis (axial)")
    w2: float = Field(default=0.0, description="Start intensity along local 2-axis (transverse)")
    w3: float = Field(default=0.0, description="Start intensity along local 3-axis (out-of-plane)")
    # Local load components (end intensity, None means uniform equal to start)
    w1_end: Optional[float] = Field(default=None, description="End intensity along local 1-axis")
    w2_end: Optional[float] = Field(default=None, description="End intensity along local 2-axis")
    w3_end: Optional[float] = Field(default=None, description="End intensity along local 3-axis")
    # Relative positions along element span [0, 1]
    start: float = Field(default=0.0, ge=0.0, le=1.0, description="Relative start position [0, 1]")
    end: float = Field(default=1.0, ge=0.0, le=1.0, description="Relative end position [0, 1]")
    is_local: bool = Field(default=False, description="Flag indicating local element coordinate system")
    is_self_weight: bool = Field(default=False, description="Flag indicating whether this load represents member self-weight")

    @model_validator(mode="before")
    @classmethod
    def _migrate_and_sync(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Check range
            st = data.get("start", 0.0)
            en = data.get("end", 1.0)
            if st is not None and en is not None:
                if float(st) < 0.0 or float(en) > 1.0 or float(st) >= float(en):
                    raise ValueError(f"DistributedLoad span range must satisfy 0 <= start < end <= 1, got start={st}, end={en}")

            # Legacy migration: w_start / w_end
            w_st = data.pop("w_start", None)
            w_en = data.pop("w_end", None)
            if w_st is not None or w_en is not None:
                # Find non-zero components among wx, wy, wz, w1, w2, w3
                nz = []
                for k in ("wx", "wy", "wz", "w1", "w2", "w3"):
                    if k in data and abs(float(data[k])) > 1e-12:
                        nz.append(k)
                if len(nz) == 1:
                    target_k = nz[0]
                    target_end_k = f"{target_k}_end"
                    if w_st is not None:
                        data[target_k] = float(w_st)
                    if w_en is not None:
                        data[target_end_k] = float(w_en)
                elif len(nz) == 0:
                    # Default to wy (or w2 if is_local)
                    target_k = "w2" if data.get("is_local") else "wy"
                    target_end_k = f"{target_k}_end"
                    if w_st is not None:
                        data[target_k] = float(w_st)
                    if w_en is not None:
                        data[target_end_k] = float(w_en)
                else:
                    raise ValueError(f"Cannot migrate w_start/w_end with multiple non-zero components: {nz}")

            is_loc = data.get("is_local", False)
            if is_loc:
                for k_loc, k_glob in (("w1", "wx"), ("w2", "wy"), ("w3", "wz"),
                                      ("w1_end", "wx_end"), ("w2_end", "wy_end"), ("w3_end", "wz_end")):
                    if k_loc in data and k_glob not in data:
                        data[k_glob] = data[k_loc]
                    elif k_glob in data and k_loc not in data:
                        data[k_loc] = data[k_glob]
        return data


class ElementPointLoad(BaseSchemaModel):
    """
    Concentrated point load/moment applied at a position along a member length.
    """
    element_id: ElementId = Field(description="Target element ID")
    position: float = Field(default=0.0, ge=0.0, le=1.0, description="Relative position along element length [0, 1]")
    fx: float = Field(default=0.0, description="Force along X-axis (global X or local 1)")
    fy: float = Field(default=0.0, description="Force along Y-axis (global Y or local 2)")
    fz: float = Field(default=0.0, description="Force along Z-axis (global Z or local 3)")
    mx: float = Field(default=0.0, description="Moment about X-axis (global X or local 1)")
    my: float = Field(default=0.0, description="Moment about Y-axis (global Y or local 2)")
    mz: float = Field(default=0.0, description="Moment about Z-axis (global Z or local 3)")
    is_local: bool = Field(default=False, description="Flag indicating local element coordinate system")


class AreaLoad(BaseSchemaModel):
    """
    Uniform floor pressure over a panel or floor level, distributed to the frame members that bound it (tributary
    area). It is not a load on shell elements: a pressure on shell elements is a :class:`ShellLoad`.
    """
    id: Optional[str] = Field(default=None, description="Unique area load identifier")
    story_elevation: Optional[float] = Field(default=None, description="Floor level / elevation (Z or Y)")
    pressure: float = Field(description="Uniform surface pressure intensity (force / area, e.g. kN/m2 or psf)")
    load_type: str = Field(description="Load nature/case: 'dead', 'live', 'snow', etc.")
    node_ids: List[NodeId] = Field(default_factory=list, description="Optional bounding polygon node IDs defining the loaded panel")
    tributary_width: Optional[float] = Field(default=None, description="Optional explicit tributary width for 2D frame projection")
    one_way: bool = Field(default=True, description="Whether one-way distribution or two-way distribution is assumed")
    span_direction_axis: str = Field(default="x", description="Direction axis of one-way slab span ('x' or 'y')")

    @field_validator("load_type", mode="before")
    @classmethod
    def _validate_area_load_type(cls, val: Any) -> str:
        if val is None:
            raise ValueError("AreaLoad requires an explicit load_type ('dead', 'live', 'snow', etc.)")
        val_str = str(val).strip().lower().replace(" ", "_").replace("-", "_")
        canon = LOAD_TYPE_SYNONYMS.get(val_str, val_str)
        if canon in VALID_LOAD_TYPES:
            return canon
        raise ValueError(
            f"Invalid area load_type {val!r}. Must be one of: {sorted(VALID_LOAD_TYPES)}"
        )


class ShellLoad(BaseSchemaModel):
    """
    Uniform load on shell elements, as force per unit area of the element (CSI "uniform load", Analysis Reference
    Manual §10.14).

    - ``direction="local_3"``: along each element's local axis 3 (normal to the element).
    - ``direction="x"``, ``"y"``, or ``"z"``: along a global axis, per unit area of the element (not of its
      projection). The sign of ``pressure`` gives the sense: gravity is ``direction="z"`` with a negative pressure.

    ``is_self_weight`` marks loads generated from the section's material weight (struct_load ``apply_self_weight``),
    so that they are not counted twice.
    """
    element_ids: List[ElementId] = Field(min_length=1, description="Loaded shell element IDs")
    pressure: float = Field(description="Load per unit area of the element (model force / length^2), signed")
    direction: Literal["local_3", "x", "y", "z"] = Field(description="Load direction: local axis 3 or a global axis")
    is_self_weight: bool = Field(default=False, description="Load generated from the self-weight of the elements")


class GroundMotion(BaseSchemaModel):
    """
    Ground motion acceleration time series record.
    """
    id: str = Field(description="Unique ground motion identifier")
    dt: float = Field(gt=0.0, description="Time step increment (seconds)")
    acc: List[float] = Field(description="Acceleration values time history series")
    name: Optional[str] = Field(default=None, description="Ground motion name (e.g. 'El Centro 1940')")


class LoadCase(BaseSchemaModel):
    """
    Logical grouping of applied point loads and element loads (e.g. 'Dead', 'Live', 'Wind').
    """
    id: LoadCaseId = Field(description="Unique load case identifier")
    name: Optional[str] = Field(default=None, description="Human-readable load case name")
    load_type: Optional[str] = Field(
        default=None,
        description="Physical load type ('dead', 'super_dead', 'live', 'roof_live', 'snow', 'wind', 'seismic', 'partition')",
    )
    direction: Optional[str] = Field(
        default=None,
        description="Global action direction ('x', 'y', 'z', '-x', '-y', '-z')",
    )
    point_loads: List[PointLoad] = Field(default_factory=list, description="List of nodal point loads")
    element_loads: List[DistributedLoad] = Field(default_factory=list, description="List of distributed element loads")
    element_point_loads: List[ElementPointLoad] = Field(default_factory=list, description="List of concentrated element point loads")
    area_loads: List[AreaLoad] = Field(default_factory=list, description="List of area/surface loads assigned to this case")
    shell_loads: List[ShellLoad] = Field(default_factory=list, description="Uniform loads on shell elements")
    include_self_weight: bool = Field(default=False, description="Whether self-weight of elements should be automatically calculated")
    auto_load: Optional[str] = Field(default=None, description="Auto lateral load standard (e.g. 'ASCE 7-22')")
    seismic_params: Optional[Dict[str, Any]] = Field(default=None, description="Auto seismic parameters dictionary")
    loaded_floor_area: Optional[Dict[float, float]] = Field(default=None, description="Loaded floor panel area per story elevation")
    unloaded_beams: Optional[List[Union[int, str]]] = Field(default=None, description="Beams at floor levels that border no closed panel")

    @field_validator("load_type", mode="before")
    @classmethod
    def _validate_load_type(cls, val: Any) -> Optional[str]:
        if val is None:
            return None
        val_str = str(val).strip().lower().replace(" ", "_").replace("-", "_")
        canon = LOAD_TYPE_SYNONYMS.get(val_str, val_str)
        if canon in VALID_LOAD_TYPES:
            return canon
        raise ValueError(
            f"Invalid load_type {val!r}. Must be one of: {sorted(VALID_LOAD_TYPES)}"
        )


class LoadCaseFactor(BaseSchemaModel):
    """
    Scale factor applied to a load case within a load combination.
    """
    load_case_id: LoadCaseId = Field(description="Referenced load case ID")
    factor: float = Field(default=1.0, description="Load factor scale multiplier")


class LoadCombination(BaseSchemaModel):
    """
    Factored linear combination of load cases (e.g. 1.2D + 1.6L).
    """
    id: str = Field(description="Unique load combination identifier")
    name: Optional[str] = Field(default=None, description="Human-readable load combination name")
    factors: List[LoadCaseFactor] = Field(default_factory=list, description="List of load cases with factors")
    kind: Literal["strength", "service"] = Field(
        default="strength",
        description="Combination limit state: 'strength' (factored) or 'service' (unfactored / serviceability)",
    )
    method: Literal["LRFD", "ASD"] = Field(
        default="LRFD",
        description="Design philosophy: 'LRFD' or 'ASD'",
    )


class MassSourceFactor(BaseSchemaModel):
    """
    Multiplier factor applied to a load case for inertial mass conversion (e.g. 1.0 for DEAD, 0.25 for LIVE).
    """
    load_case_id: LoadCaseId = Field(description="Referenced load case ID")
    factor: float = Field(default=1.0, description="Scale factor applied to load case forces for mass conversion")


class MassSource(BaseSchemaModel):
    """
    Defines inertial mass configuration for dynamic and modal analysis.
    """
    id: str = Field(default="MS1", description="Unique mass source identifier")
    name: Optional[str] = Field(default="Default Mass Source", description="Human-readable mass source name")
    include_element_mass: bool = Field(
        default=True,
        description="Whether to include element mass from material density rho * A * L",
    )
    include_added_mass: bool = Field(
        default=True,
        description="Whether to include user-assigned nodal masses and element masses",
    )
    factors: List[MassSourceFactor] = Field(
        default_factory=list,
        description="List of load cases with conversion factors into inertial mass",
    )
    lateral_only: bool = Field(
        default=False,
        description="If True, mass is assigned to horizontal translational DOFs only (UX, UY). If False, assigned to all translational DOFs.",
    )
