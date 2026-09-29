"""
Unit tests for struct_core.units module:
- Parsing
- Canonical normalization
- Conversion factor math
- Project-wide conversion (geometry, materials, sections, loads, results)
"""

import pytest
from struct_core import (
    Project, Units, PRESETS, parse_units, conversion_factor,
    convert_project_units, get_unit_labels,
)
from struct_core.structural_model import (
    Node, BeamElement, RectangularSection, CircularSection,
    GeneralSection, ElasticMaterial, BilinearMaterial,
    Support, PointLoad, DistributedLoad, LoadCase,
)
from struct_core.analysis_result import (
    AnalysisResult, NodeResult, NodeDisplacement, NodeReaction,
    ElementResult, BeamSectionForce,
)


def test_units_parse():
    u1 = parse_units("kips, in, sec")
    assert u1.force == "kip"
    assert u1.length == "in"
    assert u1.time == "s"
    assert u1.temperature == "F"

    u2 = parse_units("kN, m, sec, C")
    assert u2.force == "kN"
    assert u2.length == "m"
    assert u2.temperature == "C"

    u3 = parse_units("N, mm, s")
    assert u3.force == "N"
    assert u3.length == "mm"

    u4 = parse_units(PRESETS["kip, ft, s, °F"])
    assert u4.length == "ft"
    assert u4.force == "kip"


def test_conversion_factors():
    # Length: m to in
    f_m_in = conversion_factor("kN, m", "kip, in", "length")
    assert pytest.approx(f_m_in, rel=1e-4) == 39.3700787

    # Length: m to ft
    f_m_ft = conversion_factor("kN, m", "kip, ft", "length")
    assert pytest.approx(f_m_ft, rel=1e-4) == 3.28084

    # Force: kN to kip
    f_kn_kip = conversion_factor("kN, m", "kip, ft", "force")
    assert pytest.approx(f_kn_kip, rel=1e-4) == 0.2248089

    # Stress: kPa to ksi
    f_kpa_ksi = conversion_factor("kN, m", "kip, in", "stress")
    # 1 kPa = 0.000145038 ksi
    assert pytest.approx(f_kpa_ksi, rel=1e-4) == 0.0001450377

    # Stress: kPa to MPa (N, mm)
    f_kpa_mpa = conversion_factor("kN, m", "N, mm", "stress")
    assert pytest.approx(f_kpa_mpa, rel=1e-4) == 0.001

    # Moment: kN*m to kip*ft
    f_m_kft = conversion_factor("kN, m", "kip, ft", "moment")
    assert pytest.approx(f_m_kft, rel=1e-4) == 0.737562

    # Round trip factor should be exactly 1.0
    f_round = conversion_factor("kN, m", "kip, in", "stress") * conversion_factor("kip, in", "kN, m", "stress")
    assert pytest.approx(f_round, rel=1e-6) == 1.0


def test_unit_labels():
    labels_si = get_unit_labels("kN, m, s, C")
    assert labels_si.force == "kN"
    assert labels_si.length == "m"
    assert labels_si.disp == "mm"
    assert labels_si.moment == "kN·m"
    assert labels_si.stress == "kPa"

    labels_us = get_unit_labels("kip, in, s, F")
    assert labels_us.force == "kip"
    assert labels_us.length == "in"
    assert labels_us.disp == "in"
    assert labels_us.moment == "kip·in"
    assert labels_us.stress == "ksi"


def test_convert_project_geometry_and_results():
    # Build a portal frame in SI (m, kN)
    proj = Project()
    proj.metadata.units = Units(force="kN", length="m", time="s", temperature="C")

    # Nodes at (0, 0), (0, 3m), (5m, 3m)
    proj.model.nodes = [
        Node(id="1", x=0.0, y=0.0, z=0.0),
        Node(id="2", x=0.0, y=0.0, z=3.0),
        Node(id="3", x=5.0, y=0.0, z=3.0),
    ]
    proj.model.story_elevations = [0.0, 3.0]

    # Material: Concrete E = 25,000,000 kPa (25 GPa)
    mat = ElasticMaterial(id="CONC", name="C25", E=25_000_000.0, nu=0.2, rho=2400.0)
    proj.model.materials = [mat]

    # Section: Rectangular 0.3m x 0.5m
    sec = RectangularSection(id="B1", b=0.3, h=0.5)
    proj.model.sections = [sec]

    # Element
    elem = BeamElement(id="1", start_node="1", end_node="2", material_id="CONC", section_id="B1")
    proj.model.elements = [elem]

    # Support with spring
    supp = Support(node_id="1", ux=True, uy=True, uz=True, kx=1000.0, krz=5000.0)
    proj.model.supports = [supp]

    # Load: Point load Fz = -100 kN, Distributed load wy = -20 kN/m
    pl = PointLoad(node_id="2", fz=-100.0, my=15.0)
    dl = DistributedLoad(element_id="1", wy=-20.0)
    lc = LoadCase(id="DEAD", point_loads=[pl], element_loads=[dl])
    proj.model.load_cases = [lc]

    # Synthetic Analysis Result: disp uz = -0.005m, reaction fz = 100 kN, moment M3 = 45 kN*m
    nr = NodeResult(
        node_id="2",
        displacement=NodeDisplacement(ux=0.001, uz=-0.005),
        reaction=NodeReaction(fz=100.0, my=15.0)
    )
    er = ElementResult(
        element_id="1",
        forces=[BeamSectionForce(station=0.0, P=-100.0, Vy=20.0, Mz=45.0)],
        max_axial=100.0,
        max_moment=45.0
    )
    ar = AnalysisResult(analysis_case_id="DEAD", node_results={"2": nr}, element_results={"1": er})
    proj.analysis_results["DEAD"] = ar

    # Convert to US Customary (kip, ft, s, F)
    proj.convert_units("kip, ft, s, F")

    assert proj.metadata.units.force == "kip"
    assert proj.metadata.units.length == "ft"

    # Verify geometry converted: 3m -> 9.8425 ft, 5m -> 16.4042 ft
    assert pytest.approx(proj.model.nodes[1].z, rel=1e-4) == 3.0 * 3.28084
    assert pytest.approx(proj.model.nodes[2].x, rel=1e-4) == 5.0 * 3.28084
    assert pytest.approx(proj.model.story_elevations[1], rel=1e-4) == 3.0 * 3.28084

    # Verify section converted: 0.3m -> 0.98425 ft
    assert pytest.approx(proj.model.sections[0].b, rel=1e-4) == 0.3 * 3.28084
    assert pytest.approx(proj.model.sections[0].h, rel=1e-4) == 0.5 * 3.28084

    # Verify loads converted: -100 kN -> -22.4809 kip
    assert pytest.approx(proj.model.load_cases[0].point_loads[0].fz, rel=1e-4) == -100.0 * 0.2248089
    # wy: -20 kN/m -> kip/ft
    f_line = conversion_factor("kN, m", "kip, ft", "line_load")
    assert pytest.approx(proj.model.load_cases[0].element_loads[0].wy, rel=1e-4) == -20.0 * f_line

    # Verify analysis results converted:
    # uz: -0.005 m -> -0.016404 ft
    assert pytest.approx(proj.analysis_results["DEAD"].node_results["2"].displacement.uz, rel=1e-4) == -0.005 * 3.28084
    # reaction fz: 100 kN -> 22.4809 kip
    assert pytest.approx(proj.analysis_results["DEAD"].node_results["2"].reaction.fz, rel=1e-4) == 100.0 * 0.2248089
    # moment M3: 45 kN*m -> 33.1903 kip*ft
    f_mom = conversion_factor("kN, m", "kip, ft", "moment")
    assert pytest.approx(proj.analysis_results["DEAD"].element_results["1"].forces[0].Mz, rel=1e-4) == 45.0 * f_mom
