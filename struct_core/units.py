"""
struct_core/units.py
════════════════════
Comprehensive unit systems, physical dimensions, conversion factors,
and project-wide unit conversion for structural models and analysis results.

Supports:
- SI Metric: kN, N, m, mm, cm, C
- US Customary: kip, lbf, in, ft, F
- Any valid combination of (force, length, time, temperature).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field


# ── Canonical Unit Mappings ───────────────────────────────────────────────────

_FORCE_CANONICAL = {
    "kn": "kN", "kilonewton": "kN", "kilonewtons": "kN",
    "n": "N", "newton": "N", "newtons": "N",
    "kip": "kip", "kips": "kip", "k": "kip", "klbf": "kip",
    "lbf": "lbf", "lb": "lbf", "lbs": "lbf", "pound": "lbf", "pounds": "lbf",
    "kgf": "kgf",
    "tf": "tf", "tonf": "tf", "tonne_force": "tf",
}

_LENGTH_CANONICAL = {
    "m": "m", "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "mm": "mm", "millimeter": "mm", "millimeters": "mm",
    "cm": "cm", "centimeter": "cm", "centimeters": "cm",
    "in": "in", "inch": "in", "inches": "in",
    "ft": "ft", "foot": "ft", "feet": "ft",
}

_TIME_CANONICAL = {
    "s": "s", "sec": "s", "second": "s", "seconds": "s",
}

_TEMP_CANONICAL = {
    "c": "C", "celsius": "C", "centigrade": "C", "°c": "C",
    "f": "F", "fahrenheit": "F", "°f": "F",
    "k": "K", "kelvin": "K",
}

_MASS_CANONICAL = {
    "kg": "kg", "kilogram": "kg", "kilograms": "kg",
    "tonne": "tonne", "t": "tonne", "ton": "tonne",
    "g": "g", "gram": "g",
    "slug": "slug", "slugs": "slug",
    "lb": "lb", "lbm": "lb", "pound_mass": "lb",
}


def normalize_unit_str(val: str, category: str) -> str:
    """Normalize user input string to canonical symbol."""
    clean = val.strip().lower().replace("°", "")
    if category == "force":
        return _FORCE_CANONICAL.get(clean, val.strip())
    if category == "length":
        return _LENGTH_CANONICAL.get(clean, val.strip())
    if category == "time":
        return _TIME_CANONICAL.get(clean, val.strip())
    if category == "temperature":
        return _TEMP_CANONICAL.get(clean, val.strip().upper())
    if category == "mass":
        return _MASS_CANONICAL.get(clean, val.strip())
    return val.strip()


# ── Conversion Ratios to Base SI (N, m, s, K/°C, kg) ─────────────────────────

_FORCE_TO_N = {
    "N": 1.0,
    "kN": 1_000.0,
    "kip": 4_448.2216152605,
    "lbf": 4.4482216152605,
    "kgf": 9.80665,
    "tf": 9_806.65,
}

_LENGTH_TO_M = {
    "m": 1.0,
    "mm": 0.001,
    "cm": 0.01,
    "in": 0.0254,
    "ft": 0.3048,
}

_TIME_TO_S = {
    "s": 1.0,
}

_TEMP_DIFF_TO_C = {
    "C": 1.0,
    "K": 1.0,
    "F": 5.0 / 9.0,
}

_MASS_TO_KG = {
    "kg": 1.0,
    "tonne": 1_000.0,
    "g": 0.001,
    "slug": 14.5939029372,
    "lb": 0.45359237,
}


# ── Dimensional Powers: (force, length, time, temp_diff) ──────────────────────

DIMENSIONS: Dict[str, Tuple[int, int, int, int]] = {
    "length": (0, 1, 0, 0),
    "area": (0, 2, 0, 0),
    "volume": (0, 3, 0, 0),
    "inertia": (0, 4, 0, 0),
    "force": (1, 0, 0, 0),
    "moment": (1, 1, 0, 0),
    "line_load": (1, -1, 0, 0),
    "stress": (1, -2, 0, 0),             # pressure, stress, modulus
    "pressure": (1, -2, 0, 0),
    "trans_stiffness": (1, -1, 0, 0),
    "rot_stiffness": (1, 1, 0, 0),
    "velocity": (0, 1, -1, 0),
    "acceleration": (0, 1, -2, 0),
    "time": (0, 0, 1, 0),
    "temperature": (0, 0, 0, 1),
    "thermal_coeff": (0, 0, 0, -1),
    "mass_density": (1, -4, 2, 0),       # derived from F * T^2 / L^4
    "weight_density": (1, -3, 0, 0),     # F / L^3
}


# ── Units Schema ──────────────────────────────────────────────────────────────

class Units(BaseModel):
    """
    Engineering units system schema.
    """
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    length: str = Field(default="m", description="Length unit, e.g., 'm', 'mm', 'in', 'ft'")
    force: str = Field(default="kN", description="Force unit, e.g., 'N', 'kN', 'kip', 'lbf'")
    time: str = Field(default="s", description="Time unit, e.g., 's'")
    mass: str = Field(default="kg", description="Mass unit, e.g., 'kg', 'tonne', 'slug'")
    temperature: str = Field(default="C", description="Temperature unit, e.g., 'C', 'F', 'K'")

    def canonical(self) -> "Units":
        """Return a copy with normalized canonical unit symbols."""
        return Units(
            length=normalize_unit_str(self.length, "length"),
            force=normalize_unit_str(self.force, "force"),
            time=normalize_unit_str(self.time, "time"),
            mass=normalize_unit_str(self.mass, "mass"),
            temperature=normalize_unit_str(self.temperature, "temperature"),
        )

    @property
    def label(self) -> str:
        """Compact label for display, e.g., 'kN, m, s, °C' or 'kip, in, s, °F'."""
        temp_sym = f"°{self.temperature}" if self.temperature in ("C", "F") else self.temperature
        return f"{self.force}, {self.length}, {self.time}, {temp_sym}"

    @property
    def short_label(self) -> str:
        """Very short label: 'kN, m' or 'kip, in' or 'kip, ft'."""
        return f"{self.force}, {self.length}"

    def __str__(self) -> str:
        return self.label

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Units):
            if isinstance(other, str):
                try:
                    other = parse_units(other)
                except Exception:
                    return False
            else:
                return False
        c1 = self.canonical()
        c2 = other.canonical()
        return (c1.force == c2.force and
                c1.length == c2.length and
                c1.time == c2.time and
                c1.temperature == c2.temperature)


# Backward-compatible alias
UnitsSchema = Units


# ── Standard Engineering Presets ──────────────────────────────────────────────

PRESETS: Dict[str, Units] = {
    "kN, m, s, °C": Units(force="kN", length="m", time="s", mass="kg", temperature="C"),
    "kN, mm, s, °C": Units(force="kN", length="mm", time="s", mass="kg", temperature="C"),
    "N, mm, s, °C": Units(force="N", length="mm", time="s", mass="tonne", temperature="C"),
    "N, m, s, °C": Units(force="N", length="m", time="s", mass="kg", temperature="C"),
    "kip, in, s, °F": Units(force="kip", length="in", time="s", mass="slug", temperature="F"),
    "kip, ft, s, °F": Units(force="kip", length="ft", time="s", mass="slug", temperature="F"),
    "lbf, in, s, °F": Units(force="lbf", length="in", time="s", mass="slug", temperature="F"),
    "lbf, ft, s, °F": Units(force="lbf", length="ft", time="s", mass="slug", temperature="F"),
}


def parse_units(spec: Union[str, Dict[str, Any], Units]) -> Units:
    """
    Parse a unit specification from string, dict, or existing Units instance.
    Examples:
      - 'kips, in, sec' -> Units(force='kip', length='in', time='s', temperature='F')
      - 'kips, ft, sec' -> Units(force='kip', length='ft', time='s', temperature='F')
      - 'kN, m, sec, C' -> Units(force='kN', length='m', time='s', temperature='C')
    """
    if isinstance(spec, Units):
        return spec.canonical()

    if isinstance(spec, dict):
        return Units(
            force=normalize_unit_str(spec.get("force", "kN"), "force"),
            length=normalize_unit_str(spec.get("length", "m"), "length"),
            time=normalize_unit_str(spec.get("time", "s"), "time"),
            mass=normalize_unit_str(spec.get("mass", "kg"), "mass"),
            temperature=normalize_unit_str(spec.get("temperature", "C"), "temperature"),
        )

    text = str(spec).strip()
    # Check exact preset key
    for k, u in PRESETS.items():
        if text.lower() == k.lower().replace("°", ""):
            return u

    # Tokenize by comma, space, or slash
    tokens = [t.strip().strip(",;").replace("°", "") for t in re.split(r"[,;\s]+", text) if t.strip()]

    force = "kN"
    length = "m"
    time = "s"
    temp = "C"
    mass = "kg"

    for tok in tokens:
        clean = tok.lower()
        if clean in _FORCE_CANONICAL:
            force = _FORCE_CANONICAL[clean]
        elif clean in _LENGTH_CANONICAL:
            length = _LENGTH_CANONICAL[clean]
        elif clean in _TIME_CANONICAL:
            time = _TIME_CANONICAL[clean]
        elif clean in _TEMP_CANONICAL:
            temp = _TEMP_CANONICAL[clean]
        elif clean in _MASS_CANONICAL:
            mass = _MASS_CANONICAL[clean]

    # Infer customary temperature default if US Customary
    if force in ("kip", "lbf") and temp == "C" and "c" not in [t.lower() for t in tokens]:
        temp = "F"
        mass = "slug"

    return Units(force=force, length=length, time=time, mass=mass, temperature=temp)


# ── Conversion Factor Calculation ─────────────────────────────────────────────

def conversion_factor(
    from_units: Union[Units, str],
    to_units: Union[Units, str],
    dimension: Union[str, Tuple[int, int, int, int]]
) -> float:
    """
    Calculate the multiplicative scaling factor to convert a quantity of given
    dimension from `from_units` to `to_units`.

    scale = (val in from_units) * factor -> (val in to_units)
    """
    u_from = parse_units(from_units)
    u_to = parse_units(to_units)

    if isinstance(dimension, str):
        dim_key = dimension.lower().strip()
        if dim_key not in DIMENSIONS:
            raise KeyError(f"Unknown physical dimension '{dimension}'. Available: {list(DIMENSIONS.keys())}")
        a, b, c, d = DIMENSIONS[dim_key]
    else:
        a, b, c, d = dimension

    # Force ratio (from / to in N)
    f_from = _FORCE_TO_N.get(u_from.force, 1000.0)
    f_to = _FORCE_TO_N.get(u_to.force, 1000.0)
    force_ratio = f_from / f_to

    # Length ratio (from / to in m)
    l_from = _LENGTH_TO_M.get(u_from.length, 1.0)
    l_to = _LENGTH_TO_M.get(u_to.length, 1.0)
    length_ratio = l_from / l_to

    # Time ratio
    t_from = _TIME_TO_S.get(u_from.time, 1.0)
    t_to = _TIME_TO_S.get(u_to.time, 1.0)
    time_ratio = t_from / t_to

    # Temperature difference ratio
    th_from = _TEMP_DIFF_TO_C.get(u_from.temperature, 1.0)
    th_to = _TEMP_DIFF_TO_C.get(u_to.temperature, 1.0)
    temp_ratio = th_from / th_to

    scale = 1.0
    if a != 0:
        scale *= (force_ratio ** a)
    if b != 0:
        scale *= (length_ratio ** b)
    if c != 0:
        scale *= (time_ratio ** c)
    if d != 0:
        scale *= (temp_ratio ** d)

    return scale


# ── Formatted Unit Labels Helper ──────────────────────────────────────────────

class UnitLabels:
    """Convenience class providing standard engineering unit symbol strings for UI headers and labels."""

    def __init__(self, units: Units) -> None:
        self.u = units.canonical()
        self.force = self.u.force
        self.length = self.u.length
        self.time = self.u.time
        self.temp = f"°{self.u.temperature}" if self.u.temperature in ("C", "F") else self.u.temperature

        # Coordinate & span length
        self.coord = self.length
        self.span = self.length

        # Displacements: in or mm usually preferred
        if self.length in ("m", "mm", "cm"):
            self.disp = "mm"
            self.disp_scale = 1000.0 if self.length == "m" else (10.0 if self.length == "cm" else 1.0)
        else:
            self.disp = "in"
            self.disp_scale = 12.0 if self.length == "ft" else 1.0

        # Section dimensions
        if self.length in ("m", "mm", "cm"):
            self.sec_dim = "mm"
            self.area = "mm²" if self.length == "mm" else "m²"
            self.inertia = "mm⁴" if self.length == "mm" else "m⁴"
        else:
            self.sec_dim = "in"
            self.area = "in²" if self.length == "in" else "ft²"
            self.inertia = "in⁴" if self.length == "in" else "ft⁴"

        # Moments
        self.moment = f"{self.force}·{self.length}"

        # Distributed line load
        self.line_load = f"{self.force}/{self.length}"

        # Stress / Elastic Modulus
        if self.force == "kN" and self.length == "m":
            self.stress = "kPa"
            self.modulus = "kPa"
        elif self.force == "N" and self.length == "mm":
            self.stress = "MPa"
            self.modulus = "MPa"
        elif self.force == "kN" and self.length == "mm":
            self.stress = "GPa"
            self.modulus = "GPa"
        elif self.force == "kip" and self.length == "in":
            self.stress = "ksi"
            self.modulus = "ksi"
        elif self.force == "kip" and self.length == "ft":
            self.stress = "ksf"
            self.modulus = "ksf"
        elif self.force == "lbf" and self.length == "in":
            self.stress = "psi"
            self.modulus = "psi"
        elif self.force == "lbf" and self.length == "ft":
            self.stress = "psf"
            self.modulus = "psf"
        else:
            self.stress = f"{self.force}/{self.length}²"
            self.modulus = f"{self.force}/{self.length}²"

        # Surface pressure / Area load
        if self.force == "kN" and self.length == "m":
            self.pressure = "kN/m²"
        elif self.force == "kip" and self.length == "ft":
            self.pressure = "ksf"
        elif self.force == "lbf" and self.length == "ft":
            self.pressure = "psf"
        elif self.force == "kip" and self.length == "in":
            self.pressure = "ksi"
        else:
            self.pressure = f"{self.force}/{self.length}²"

        # Density
        if self.length == "m":
            self.density = "kg/m³"
        elif self.length in ("in", "ft"):
            self.density = "pcf" if self.length == "ft" else "lb/in³"
        else:
            self.density = f"{self.u.mass}/{self.length}³"


def get_unit_labels(units: Union[Units, str]) -> UnitLabels:
    """Return formatted UnitLabels instance for the given units."""
    return UnitLabels(parse_units(units))


# ── Full Project Unit Conversion ──────────────────────────────────────────────

def convert_project_units(
    project: Any,
    to_units: Union[Units, str, Dict[str, Any]],
    in_place: bool = True
) -> Any:
    """
    Convert an entire `struct_core.Project` and its `StructuralModel` and
    `AnalysisResult`s from current `project.metadata.units` to `to_units`.

    Every numerical value representing coordinates, spans, sections, materials,
    loads, and results is automatically scaled by its physical dimension.
    """
    target_units = parse_units(to_units)

    current_units = getattr(getattr(project, "metadata", None), "units", None)
    if current_units is None:
        source_units = Units()
    else:
        source_units = parse_units(current_units)

    # If identical, nothing to do
    if source_units == target_units:
        if getattr(project, "metadata", None) is not None:
            project.metadata.units = target_units
        return project

    target_proj = project if in_place else project.model_copy(deep=True)

    # Compute conversion scale factors
    f_len = conversion_factor(source_units, target_units, "length")
    f_area = conversion_factor(source_units, target_units, "area")
    f_inertia = conversion_factor(source_units, target_units, "inertia")
    f_force = conversion_factor(source_units, target_units, "force")
    f_moment = conversion_factor(source_units, target_units, "moment")
    f_line_load = conversion_factor(source_units, target_units, "line_load")
    f_stress = conversion_factor(source_units, target_units, "stress")
    f_trans_stiff = conversion_factor(source_units, target_units, "trans_stiffness")
    f_rot_stiff = conversion_factor(source_units, target_units, "rot_stiffness")
    f_density = conversion_factor(source_units, target_units, "mass_density")

    model = getattr(target_proj, "model", None)
    if model is not None:
        # 1. Nodes (x, y, z)
        for node in getattr(model, "nodes", []):
            if hasattr(node, "x") and node.x is not None:
                node.x = float(node.x) * f_len
            if hasattr(node, "y") and node.y is not None:
                node.y = float(node.y) * f_len
            if hasattr(node, "z") and node.z is not None:
                node.z = float(node.z) * f_len

        # 2. Story Elevations
        if hasattr(model, "story_elevations") and model.story_elevations:
            model.story_elevations = [float(h) * f_len for h in model.story_elevations]

        # 3. Materials (E, Et, fy, fc, rho)
        for mat in getattr(model, "materials", []):
            if hasattr(mat, "E") and mat.E is not None:
                mat.E = float(mat.E) * f_stress
            if hasattr(mat, "Et") and mat.Et is not None:
                mat.Et = float(mat.Et) * f_stress
            if hasattr(mat, "fy") and mat.fy is not None:
                mat.fy = float(mat.fy) * f_stress
            if hasattr(mat, "fc") and mat.fc is not None:
                mat.fc = float(mat.fc) * f_stress
            if hasattr(mat, "rho") and mat.rho is not None:
                mat.rho = float(mat.rho) * f_density

        # 4. Sections (b, h, d, A, Iz, Iy, J)
        for sec in getattr(model, "sections", []):
            sec_type = getattr(sec, "type", "")
            if sec_type == "rectangular" or (hasattr(sec, "b") and hasattr(sec, "h")):
                if hasattr(sec, "b") and sec.b is not None:
                    sec.b = float(sec.b) * f_len
                if hasattr(sec, "h") and sec.h is not None:
                    sec.h = float(sec.h) * f_len
            elif sec_type == "circular" or hasattr(sec, "d"):
                if hasattr(sec, "d") and sec.d is not None:
                    sec.d = float(sec.d) * f_len
            elif sec_type == "general" or hasattr(sec, "A"):
                if hasattr(sec, "A") and sec.A is not None:
                    sec.A = float(sec.A) * f_area
                if hasattr(sec, "Iz") and sec.Iz is not None:
                    sec.Iz = float(sec.Iz) * f_inertia
                if hasattr(sec, "Iy") and sec.Iy is not None:
                    sec.Iy = float(sec.Iy) * f_inertia
                if hasattr(sec, "J") and sec.J is not None:
                    sec.J = float(sec.J) * f_inertia

        # 5. Supports (kx, ky, kz, krx, kry, krz)
        for supp in getattr(model, "supports", []):
            for attr in ("kx", "ky", "kz"):
                val = getattr(supp, attr, None)
                if val is not None and float(val) > 0:
                    setattr(supp, attr, float(val) * f_trans_stiff)
            for attr in ("krx", "kry", "krz"):
                val = getattr(supp, attr, None)
                if val is not None and float(val) > 0:
                    setattr(supp, attr, float(val) * f_rot_stiff)

        # 6. Load Cases
        for lc in getattr(model, "load_cases", []):
            # Point loads
            for pl in getattr(lc, "point_loads", []):
                for f_attr in ("fx", "fy", "fz"):
                    v = getattr(pl, f_attr, None)
                    if v is not None:
                        setattr(pl, f_attr, float(v) * f_force)
                for m_attr in ("mx", "my", "mz"):
                    v = getattr(pl, m_attr, None)
                    if v is not None:
                        setattr(pl, m_attr, float(v) * f_moment)

            # Element loads
            for dl in getattr(lc, "element_loads", []):
                for w_attr in ("wx", "wy", "wz", "w1", "w2"):
                    v = getattr(dl, w_attr, None)
                    if v is not None:
                        setattr(dl, w_attr, float(v) * f_line_load)

            # Area loads inside case
            for al in getattr(lc, "area_loads", []):
                if hasattr(al, "pressure") and al.pressure is not None:
                    al.pressure = float(al.pressure) * f_stress
                if hasattr(al, "story_elevation") and al.story_elevation is not None:
                    al.story_elevation = float(al.story_elevation) * f_len
                if hasattr(al, "tributary_width") and al.tributary_width is not None:
                    al.tributary_width = float(al.tributary_width) * f_len

        # Top-level area loads
        for al in getattr(model, "area_loads", []):
            if hasattr(al, "pressure") and al.pressure is not None:
                al.pressure = float(al.pressure) * f_stress
            if hasattr(al, "story_elevation") and al.story_elevation is not None:
                al.story_elevation = float(al.story_elevation) * f_len
            if hasattr(al, "tributary_width") and al.tributary_width is not None:
                al.tributary_width = float(al.tributary_width) * f_len

    # 7. Analysis Results
    analysis_results_dict = getattr(target_proj, "analysis_results", {})
    if isinstance(analysis_results_dict, dict):
        for case_id, a_res in analysis_results_dict.items():
            # Node results
            for nid, nr in getattr(a_res, "node_results", {}).items():
                disp = getattr(nr, "displacement", None)
                if disp is not None:
                    for u_attr in ("ux", "uy", "uz"):
                        v = getattr(disp, u_attr, None)
                        if v is not None:
                            setattr(disp, u_attr, float(v) * f_len)
                reac = getattr(nr, "reaction", None)
                if reac is not None:
                    for f_attr in ("fx", "fy", "fz"):
                        v = getattr(reac, f_attr, None)
                        if v is not None:
                            setattr(reac, f_attr, float(v) * f_force)
                    for m_attr in ("mx", "my", "mz"):
                        v = getattr(reac, m_attr, None)
                        if v is not None:
                            setattr(reac, m_attr, float(v) * f_moment)

            # Element results
            for eid, er in getattr(a_res, "element_results", {}).items():
                for sf in getattr(er, "forces", []):
                    if hasattr(sf, "station") and sf.station is not None:
                        sf.station = float(sf.station) * f_len
                    if hasattr(sf, "P") and sf.P is not None:
                        sf.P = float(sf.P) * f_force
                    for v_attr in ("Vy", "Vz", "v2", "v3", "shear"):
                        if hasattr(sf, v_attr) and getattr(sf, v_attr) is not None:
                            setattr(sf, v_attr, float(getattr(sf, v_attr)) * f_force)
                    for m_attr in ("My", "Mz", "m2", "m3", "moment", "T", "t"):
                        if hasattr(sf, m_attr) and getattr(sf, m_attr) is not None:
                            setattr(sf, m_attr, float(getattr(sf, m_attr)) * f_moment)

                if hasattr(er, "max_axial") and er.max_axial is not None:
                    er.max_axial = float(er.max_axial) * f_force
                if hasattr(er, "max_shear") and er.max_shear is not None:
                    er.max_shear = float(er.max_shear) * f_force
                if hasattr(er, "max_moment") and er.max_moment is not None:
                    er.max_moment = float(er.max_moment) * f_moment

    # Update Project metadata units
    if getattr(target_proj, "metadata", None) is not None:
        target_proj.metadata.units = target_units

    return target_proj
