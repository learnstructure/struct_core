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
    "mn": "MN", "meganewton": "MN", "meganewtons": "MN",
    "n": "N", "newton": "N", "newtons": "N",
    "kip": "kip", "kips": "kip", "k": "kip", "klbf": "kip",
    "lbf": "lbf", "lb": "lbf", "lbs": "lbf", "pound": "lbf", "pounds": "lbf",
    "kgf": "kgf",
    "tf": "tf", "tonf": "tf", "tonne_force": "tf",
}

_LENGTH_CANONICAL = {
    "m": "m", "meter": "m", "meters": "m", "metre": "m", "metres": "m",
    "km": "km", "kilometer": "km", "kilometers": "km",
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
    "MN": 1_000_000.0,
    "kip": 4_448.2216152605,
    "lbf": 4.4482216152605,
    "kgf": 9.80665,
    "tf": 9_806.65,
}

_LENGTH_TO_M = {
    "m": 1.0,
    "km": 1_000.0,
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
    "mass": (0, 0, 0, 0),                # M
    "mass_density": (1, -4, 2, 0),       # M / L^3 (handled via canonical mass and length units)
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
        """Compact label for display, e.g., 'kN, m, s, kg, °C' or 'kip, in, s, slug, °F'."""
        temp_sym = f"°{self.temperature}" if self.temperature in ("C", "F") else self.temperature
        return f"{self.force}, {self.length}, {self.time}, {self.mass}, {temp_sym}"

    @property
    def short_label(self) -> str:
        """Very short label: 'kN, m' or 'kip, in' or 'kip, ft'."""
        return f"{self.force}, {self.length}"

    @property
    def is_metric(self) -> bool:
        """True if the unit system is metric (m, mm, cm)."""
        return self.canonical().length in ("m", "mm", "cm")

    @property
    def is_us_customary(self) -> bool:
        """True if the unit system is US Customary (in, ft)."""
        return self.canonical().length in ("in", "ft")

    @property
    def gravity_acceleration(self) -> float:
        """
        Standard gravitational acceleration g in the active length/time units.
        - m/s^2: 9.80665
        - mm/s^2: 9806.65
        - cm/s^2: 980.665
        - in/s^2: 386.08858
        - ft/s^2: 32.17405
        """
        c = self.canonical()
        len_to_m = _LENGTH_TO_M.get(c.length, 1.0)
        time_to_s = _TIME_TO_S.get(c.time, 1.0)
        return (9.80665 / len_to_m) * (time_to_s ** 2)

    @property
    def consistent_mass_factor(self) -> float:
        """
        Multiplicative factor to convert mass from `self.mass` (e.g. kg, tonne, slug, lb)
        into consistent dynamic mass: [F] * [T]^2 / [L].

        Example:
          - (kN, m, s, kg): 1 kg * 0.001 = 0.001 kN*s^2/m (metric tonne)
          - (N, m, s, kg): 1 kg * 1.0 = 1.0 N*s^2/m (kg)
          - (N, mm, s, tonne): 1 tonne * 1.0 = 1.0 N*s^2/mm (tonne)
          - (kip, in, s, slug): 1 slug * (1/12000) = 8.333e-5 kip*s^2/in
          - (lbf, ft, s, slug): 1 slug * 1.0 = 1.0 slug
          - (lbf, in, s, slug): 1 slug * (1/12) = 0.08333 lbf*s^2/in
        """
        c = self.canonical()
        m_to_kg = _MASS_TO_KG.get(c.mass, 1.0)
        len_to_m = _LENGTH_TO_M.get(c.length, 1.0)
        f_to_n = _FORCE_TO_N.get(c.force, 1.0)
        time_to_s = _TIME_TO_S.get(c.time, 1.0)
        return (m_to_kg * len_to_m) / (f_to_n * (time_to_s ** 2))

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
                c1.mass == c2.mass and
                c1.temperature == c2.temperature)

    @classmethod
    def from_string(cls, spec: Union[str, Dict[str, Any], "Units"]) -> "Units":
        """
        Parse a unit specification from string, dict, or existing Units instance.
        Examples:
          - Units.from_string("kN, m")
          - Units.from_string("kip, in")
          - Units.from_string("N, mm")
        """
        return parse_units(spec)




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
    "si": Units(force="kN", length="m", time="s", mass="kg", temperature="C"),
    "us": Units(force="kip", length="in", time="s", mass="slug", temperature="F"),
    "metric": Units(force="kN", length="m", time="s", mass="kg", temperature="C"),
    "customary": Units(force="kip", length="in", time="s", mass="slug", temperature="F"),
}


def parse_units(spec: Union[str, Dict[str, Any], Units]) -> Units:
    """
    Parse a unit specification from string, dict, or existing Units instance.
    Examples:
      - 'kips, in, sec' -> Units(force='kip', length='in', time='s', mass='slug', temperature='F')
      - 'kips, ft, sec' -> Units(force='kip', length='ft', time='s', mass='slug', temperature='F')
      - 'kN, m, sec, C' -> Units(force='kN', length='m', time='s', mass='kg', temperature='C')
    """
    if isinstance(spec, Units):
        return spec.canonical()

    if isinstance(spec, dict):
        force_raw = spec.get("force", "kN")
        length_raw = spec.get("length", "m")
        force = normalize_unit_str(force_raw, "force")
        length = normalize_unit_str(length_raw, "length")
        time = normalize_unit_str(spec.get("time", "s"), "time")

        if "mass" in spec:
            mass = normalize_unit_str(spec["mass"], "mass")
        elif force in ("kip", "lbf"):
            mass = "slug"
        elif force == "N" and length == "mm":
            mass = "tonne"
        else:
            mass = "kg"

        if "temperature" in spec:
            temp = normalize_unit_str(spec["temperature"], "temperature")
        elif force in ("kip", "lbf"):
            temp = "F"
        else:
            temp = "C"

        return Units(force=force, length=length, time=time, mass=mass, temperature=temp)

    text = str(spec).strip()
    if text.lower() == "si":
        return Units(force="kN", length="m", time="s", mass="kg", temperature="C")
    if text.lower() == "us":
        return Units(force="kip", length="in", time="s", mass="slug", temperature="F")

    # Check exact preset key
    for k, u in PRESETS.items():
        if text.lower() == k.lower().replace("°", ""):
            return u

    # Tokenize by comma, semicolon, or whitespace
    tokens = [t.strip().strip(",;").replace("°", "") for t in re.split(r"[,;\s]+", text) if t.strip()]
    if not tokens:
        raise ValueError(f"Empty unit specification: '{spec}'")

    force = None
    length = None
    time = None
    temp = None
    mass = None

    for tok in tokens:
        clean = tok.lower()
        matched = False

        # Check unambiguous mass first if clean == "lb" and force already parsed
        if clean in ("slug", "slugs", "tonne", "t", "ton", "kg", "kilogram", "kilograms", "g", "gram", "lbm", "pound_mass"):
            mass = _MASS_CANONICAL[clean]
            matched = True
        elif clean in _FORCE_CANONICAL:
            if clean in ("lb", "lbs", "pound", "pounds") and force is not None:
                mass = _MASS_CANONICAL["lb"]
            else:
                force = _FORCE_CANONICAL[clean]
            matched = True
        elif clean in _LENGTH_CANONICAL:
            length = _LENGTH_CANONICAL[clean]
            matched = True
        elif clean in _TIME_CANONICAL:
            time = _TIME_CANONICAL[clean]
            matched = True
        elif clean in _TEMP_CANONICAL:
            temp = _TEMP_CANONICAL[clean]
            matched = True
        elif clean in _MASS_CANONICAL:
            mass = _MASS_CANONICAL[clean]
            matched = True

        if not matched:
            raise ValueError(f"Unknown unit token '{tok}' in unit specification '{spec}'")

    force = force or "kN"
    length = length or "m"
    time = time or "s"

    if mass is None:
        if force in ("kip", "lbf"):
            mass = "slug"
        elif force == "N" and length == "mm":
            mass = "tonne"
        else:
            mass = "kg"

    if temp is None:
        if force in ("kip", "lbf"):
            temp = "F"
        else:
            temp = "C"

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
        if dim_key == "mass":
            m_from = _MASS_TO_KG[u_from.canonical().mass]
            m_to = _MASS_TO_KG[u_to.canonical().mass]
            return m_from / m_to
        if dim_key == "mass_density":
            m_from = _MASS_TO_KG[u_from.canonical().mass]
            m_to = _MASS_TO_KG[u_to.canonical().mass]
            l_from = _LENGTH_TO_M[u_from.canonical().length]
            l_to = _LENGTH_TO_M[u_to.canonical().length]
            return (m_from / m_to) / ((l_from / l_to) ** 3)
        a, b, c, d = DIMENSIONS[dim_key]
    else:
        a, b, c, d = dimension

    # Force ratio (from / to in N)
    if u_from.force not in _FORCE_TO_N:
        raise ValueError(f"Unsupported force unit '{u_from.force}'. Supported: {list(_FORCE_TO_N.keys())}")
    if u_to.force not in _FORCE_TO_N:
        raise ValueError(f"Unsupported force unit '{u_to.force}'. Supported: {list(_FORCE_TO_N.keys())}")
    force_ratio = _FORCE_TO_N[u_from.force] / _FORCE_TO_N[u_to.force]

    # Length ratio (from / to in m)
    if u_from.length not in _LENGTH_TO_M:
        raise ValueError(f"Unsupported length unit '{u_from.length}'. Supported: {list(_LENGTH_TO_M.keys())}")
    if u_to.length not in _LENGTH_TO_M:
        raise ValueError(f"Unsupported length unit '{u_to.length}'. Supported: {list(_LENGTH_TO_M.keys())}")
    length_ratio = _LENGTH_TO_M[u_from.length] / _LENGTH_TO_M[u_to.length]

    # Time ratio
    if u_from.time not in _TIME_TO_S:
        raise ValueError(f"Unsupported time unit '{u_from.time}'. Supported: {list(_TIME_TO_S.keys())}")
    if u_to.time not in _TIME_TO_S:
        raise ValueError(f"Unsupported time unit '{u_to.time}'. Supported: {list(_TIME_TO_S.keys())}")
    time_ratio = _TIME_TO_S[u_from.time] / _TIME_TO_S[u_to.time]

    # Temperature difference ratio
    if u_from.temperature not in _TEMP_DIFF_TO_C:
        raise ValueError(f"Unsupported temperature unit '{u_from.temperature}'. Supported: {list(_TEMP_DIFF_TO_C.keys())}")
    if u_to.temperature not in _TEMP_DIFF_TO_C:
        raise ValueError(f"Unsupported temperature unit '{u_to.temperature}'. Supported: {list(_TEMP_DIFF_TO_C.keys())}")
    temp_ratio = _TEMP_DIFF_TO_C[u_from.temperature] / _TEMP_DIFF_TO_C[u_to.temperature]

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

def _scale(obj: Any, attrs: Tuple[str, ...], factor: float) -> None:
    """Multiply each present, non-None attribute of ``obj`` by ``factor``."""
    for attr in attrs:
        value = getattr(obj, attr, None)
        if value is not None:
            setattr(obj, attr, float(value) * factor)


def _convert_materials(materials: Any, source_units: Units, target_units: Units, done: set) -> None:
    """Convert material moduli, strengths and densities in place, skipping objects already in ``done`` (a material
    object shared by the model and a design record is converted once)."""
    f_stress = conversion_factor(source_units, target_units, "stress")
    f_weight = conversion_factor(source_units, target_units, "weight_density")
    f_density = conversion_factor(source_units, target_units, "mass_density")

    for mat in materials:
        if id(mat) in done:
            continue
        done.add(id(mat))
        _scale(mat, ("E", "Et", "fy", "fu", "fc"), f_stress)
        _scale(mat, ("rho",), f_density)
        _scale(mat, ("unit_weight",), f_weight)


def _convert_sections(sections: Any, source_units: Units, target_units: Units, done: set) -> None:
    """Convert section dimensions and properties in place, skipping objects already in ``done``."""
    f_len = conversion_factor(source_units, target_units, "length")
    f_area = conversion_factor(source_units, target_units, "area")
    f_inertia = conversion_factor(source_units, target_units, "inertia")
    for sec in sections:
        if id(sec) in done:
            continue
        done.add(id(sec))
        if getattr(sec, "type", "") == "general":
            _scale(sec, ("A", "As2", "As3"), f_area)
            _scale(sec, ("I2", "I3", "J"), f_inertia)
        else:  # rectangular (b, h) and circular (d); As2 / As3 of these are derived properties
            _scale(sec, ("b", "h", "d"), f_len)
        _scale(sec, ("cover",), f_len)


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
        project.units = target_units
        return project

    target_proj = project if in_place else project.model_copy(deep=True)

    # Compute conversion scale factors
    f_len = conversion_factor(source_units, target_units, "length")
    f_force = conversion_factor(source_units, target_units, "force")
    f_moment = conversion_factor(source_units, target_units, "moment")
    f_line_load = conversion_factor(source_units, target_units, "line_load")
    f_stress = conversion_factor(source_units, target_units, "stress")
    f_trans_stiff = conversion_factor(source_units, target_units, "trans_stiffness")
    f_rot_stiff = conversion_factor(source_units, target_units, "rot_stiffness")
    f_pressure = conversion_factor(source_units, target_units, "pressure")
    converted: set = set()  # ids of material / section objects already converted

    model = getattr(target_proj, "model", None)
    if model is not None:
        # 1. Nodes (x, y, z, mass, inertia)
        f_mass = conversion_factor(source_units, target_units, "mass")
        f_node_inertia = f_mass * (f_len ** 2)

        for node in getattr(model, "nodes", []):
            if hasattr(node, "x") and node.x is not None:
                node.x = float(node.x) * f_len
            if hasattr(node, "y") and node.y is not None:
                node.y = float(node.y) * f_len
            if hasattr(node, "z") and node.z is not None:
                node.z = float(node.z) * f_len
            if hasattr(node, "mass") and node.mass is not None:
                node.mass = float(node.mass) * f_mass
            if hasattr(node, "inertia") and node.inertia is not None:
                node.inertia = float(node.inertia) * f_node_inertia

        # 2. Base elevation and named stories
        if getattr(model, "base_elevation", None) is not None:
            model.base_elevation = float(model.base_elevation) * f_len
        if getattr(model, "stories", None):
            for story in model.stories:
                story.elevation = float(story.elevation) * f_len

        # 3. Materials (E, Et, fy, fu, fc, rho, unit_weight)
        _convert_materials(getattr(model, "materials", []), source_units, target_units, converted)

        # 4. Sections (b, h, d, cover, A, As2, As3, I2, I3, J)
        _convert_sections(getattr(model, "sections", []), source_units, target_units, converted)
        for ssec in getattr(model, "shell_sections", []):
            _scale(ssec, ("thickness", "bending_thickness"), f_len)

        # 5. Supports (kx, ky, kz, krx, kry, krz) and Spring Elements (kx, ky, kz)
        for supp in getattr(model, "supports", []):
            for attr in ("kx", "ky", "kz"):
                val = getattr(supp, attr, None)
                if val is not None and float(val) > 0:
                    setattr(supp, attr, float(val) * f_trans_stiff)
            for attr in ("krx", "kry", "krz"):
                val = getattr(supp, attr, None)
                if val is not None and float(val) > 0:
                    setattr(supp, attr, float(val) * f_rot_stiff)

        for elem in getattr(model, "elements", []):
            if getattr(elem, "type", "") == "spring":
                _scale(elem, ("kx", "ky", "kz"), f_trans_stiff)

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
                for w_attr in ("wx", "wy", "wz", "wx_end", "wy_end", "wz_end",
                               "w1", "w2", "w3", "w1_end", "w2_end", "w3_end"):
                    v = getattr(dl, w_attr, None)
                    if v is not None:
                        setattr(dl, w_attr, float(v) * f_line_load)

            # Element point loads
            for epl in getattr(lc, "element_point_loads", []):
                for f_attr in ("fx", "fy", "fz"):
                    v = getattr(epl, f_attr, None)
                    if v is not None:
                        setattr(epl, f_attr, float(v) * f_force)
                for m_attr in ("mx", "my", "mz"):
                    v = getattr(epl, m_attr, None)
                    if v is not None:
                        setattr(epl, m_attr, float(v) * f_moment)

            # Uniform loads on shell elements (force per area)
            for sl in getattr(lc, "shell_loads", []):
                sl.pressure = float(sl.pressure) * f_pressure

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
    def _scale_reaction(reac: Any) -> None:
        if reac is None or id(reac) in converted:
            return
        converted.add(id(reac))
        _scale(reac, ("fx", "fy", "fz"), f_force)
        _scale(reac, ("mx", "my", "mz"), f_moment)

    def _scale_section_force(sf: Any) -> None:
        if sf is None or id(sf) in converted:
            return
        converted.add(id(sf))
        # Note: station is normalized (0.0 to 1.0) along member length; do not scale station!
        _scale(sf, ("P", "V2", "V3"), f_force)
        _scale(sf, ("M2", "M3", "T"), f_moment)

    analysis_results_dict = getattr(target_proj, "analysis_results", {})
    if isinstance(analysis_results_dict, dict):
        for case_id, a_res in analysis_results_dict.items():
            # Node results
            for nid, nr in getattr(a_res, "node_results", {}).items():
                disp = getattr(nr, "displacement", None)
                if disp is not None:
                    _scale(disp, ("ux", "uy", "uz"), f_len)
                _scale_reaction(getattr(nr, "reaction", None))
                for comb_reac in (getattr(nr, "combination_reactions", None) or {}).values():
                    _scale_reaction(comb_reac)

            # Element results
            for eid, er in getattr(a_res, "element_results", {}).items():
                for sf in getattr(er, "forces", []):
                    _scale_section_force(sf)
                for comb_stations in (getattr(er, "combination_forces", None) or {}).values():
                    for sf in comb_stations:
                        _scale_section_force(sf)

                _scale(er, ("max_axial", "max_shear"), f_force)
                _scale(er, ("max_moment",), f_moment)

            # Shell resultants: F and V are force per length, M is moment per length (force)
            def _scale_shell_forces(sf: Any) -> None:
                if sf is None or id(sf) in converted:
                    return
                converted.add(id(sf))
                _scale(sf, ("F11", "F22", "F12", "V13", "V23"), f_line_load)
                _scale(sf, ("M11", "M22", "M12"), f_force)

            for sr in getattr(a_res, "shell_results", {}).values():
                for sf in list(sr.gauss_points) + list(sr.corners):
                    _scale_shell_forces(sf)
                for comb_corners in (sr.combination_corners or {}).values():
                    for sf in comb_corners:
                        _scale_shell_forces(sf)
            for groups in getattr(a_res, "shell_node_results", {}).values():
                for g in groups:
                    _scale_shell_forces(g.forces)

            # Dynamic time history integration results
            th_res = getattr(a_res, "time_history_result", None)
            if th_res is not None:
                for step in getattr(th_res, "time_steps", []):
                    for disp in getattr(step, "displacements", {}).values():
                        _scale(disp, ("ux", "uy", "uz"), f_len)

    # 8. Design and Detailing results
    f_area = conversion_factor(source_units, target_units, "area")
    for d_res in (getattr(target_proj, "design_results", None) or {}).values():
        if getattr(d_res, "units", None) is not None:
            continue
        inputs = getattr(d_res, "inputs", None)
        if inputs is not None:
            _convert_materials(inputs.materials, source_units, target_units, converted)
            _convert_sections(inputs.sections, source_units, target_units, converted)
            _scale(inputs, ("allowable_bearing_pressure",), conversion_factor(source_units, target_units, "pressure"))
            _scale(inputs, ("footing_cover", "soil_depth"), f_len)
            _scale(inputs, ("soil_unit_weight",),
                   conversion_factor(source_units, target_units, "weight_density"))

        for edr in getattr(d_res, "element_results", {}).values():
            if getattr(edr, "flexure", None) is not None:
                _scale(edr.flexure, ("required_steel_area", "provided_steel_area"), f_area)
                _scale(edr.flexure, ("phi_mn", "mu"), f_moment)
                _scale(edr.flexure, ("neutral_axis_depth",), f_len)
            if getattr(edr, "shear", None) is not None:
                _scale(edr.shear, ("required_shear_steel", "provided_shear_steel"), f_len)
                _scale(edr.shear, ("phi_vc", "phi_vs", "phi_vn", "vu"), f_force)

    for det_res in (getattr(target_proj, "detailing_results", None) or {}).values():
        if getattr(det_res, "units", None) is not None:
            continue
        for ed in getattr(det_res, "element_results", {}).values():
            bl = getattr(ed, "bar_layout", None)
            if bl is not None:
                for layer in (getattr(bl, "top_layers", []) + getattr(bl, "bottom_layers", [])):
                    _scale(layer, ("depth",), f_len)
                    for bar in getattr(layer, "bars", []):
                        _scale(bar, ("length",), f_len)
                        _scale(bar, ("weight",), f_force)
                for stirrup in getattr(bl, "stirrups", []):
                    _scale(stirrup, ("spacing", "start_zone", "end_zone"), f_len)
            bs = getattr(ed, "bar_schedule", None)
            if bs is not None:
                _scale(bs, ("total_weight",), f_force)
                for item in getattr(bs, "items", []):
                    _scale(item, ("cut_length", "total_length"), f_len)
                    _scale(item, ("weight",), f_force)
            anch = getattr(ed, "anchorage", None)
            if anch is not None:
                _scale(anch, (
                    "development_length_tension",
                    "development_length_compression",
                    "lap_splice_length",
                    "hook_length",
                ), f_len)

    # 9. Seismic design basis
    sb = getattr(target_proj, "seismic_basis", None)
    if sb is not None and getattr(sb, "elf_inputs", None):
        if "flat_roof_snow_pressure" in sb.elf_inputs and sb.elf_inputs["flat_roof_snow_pressure"] is not None:
            sb.elf_inputs["flat_roof_snow_pressure"] = float(sb.elf_inputs["flat_roof_snow_pressure"]) * f_stress
        if "tributary_width" in sb.elf_inputs and sb.elf_inputs["tributary_width"] is not None:
            sb.elf_inputs["tributary_width"] = float(sb.elf_inputs["tributary_width"]) * f_len
        sb.elf_inputs.pop("units", None)

    # Update Project units (sole authority updating metadata and model)
    target_proj.units = target_units

    return target_proj
