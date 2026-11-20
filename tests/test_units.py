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
    from struct_core import Story
    proj.model.base_elevation = 0.0
    proj.model.stories = [Story(name="Story1", elevation=3.0)]

    # Material: Concrete E = 25,000,000 kPa (25 GPa)
    mat = ElasticMaterial(id="CONC", name="C25", E=25_000_000.0, nu=0.2, rho=2400.0)
    proj.model.materials = [mat]

    # Section: Rectangular 0.3m x 0.5m
    sec = RectangularSection(id="B1", b=0.3, h=0.5, material_id="CONC")
    proj.model.sections = [sec]

    # Element
    elem = BeamElement(id="1", start_node="1", end_node="2", section_id="B1")
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
    assert pytest.approx(proj.model.base_elevation, abs=1e-9) == 0.0
    assert proj.model.stories[0].name == "Story1"
    assert pytest.approx(proj.model.stories[0].elevation, rel=1e-4) == 3.0 * 3.28084

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


def test_units_properties_and_gravity():
    u_m = Units(length="m", force="kN", time="s")
    assert u_m.is_metric is True
    assert u_m.is_us_customary is False
    assert pytest.approx(u_m.gravity_acceleration, rel=1e-5) == 9.80665

    u_mm = Units(length="mm", force="N", time="s")
    assert u_mm.is_metric is True
    assert pytest.approx(u_mm.gravity_acceleration, rel=1e-5) == 9806.65

    u_in = Units(length="in", force="kip", time="s")
    assert u_in.is_metric is False
    assert u_in.is_us_customary is True
    assert pytest.approx(u_in.gravity_acceleration, rel=1e-5) == 386.08858

    u_ft = Units(length="ft", force="kip", time="s")
    assert u_ft.is_metric is False
    assert u_ft.is_us_customary is True
    assert pytest.approx(u_ft.gravity_acceleration, rel=1e-5) == 32.17405

    # Consistent dynamic mass factor
    assert pytest.approx(u_m.consistent_mass_factor, rel=1e-5) == 0.001
    u_n_m = Units(length="m", force="N", time="s", mass="kg")
    assert pytest.approx(u_n_m.consistent_mass_factor, rel=1e-5) == 1.0
    u_n_mm = Units(length="mm", force="N", time="s", mass="tonne")
    assert pytest.approx(u_n_mm.consistent_mass_factor, rel=1e-5) == 1.0
    u_kip_in = Units(length="in", force="kip", time="s", mass="slug")
    assert pytest.approx(u_kip_in.consistent_mass_factor, rel=1e-5) == 1.0 / 12000.0

    # Preset parsing
    assert Units.from_string("si").force == "kN"
    assert Units.from_string("si").length == "m"
    assert Units.from_string("us").force == "kip"
    assert Units.from_string("us").length == "in"


def test_convert_reinforced_concrete_inputs():
    """Strengths, weight densities, cover, general-section shear areas and recorded design inputs all convert."""
    from struct_core import (ConcreteMaterial, DesignInputs, DesignResult, GeneralSection, Project, RebarMaterial,
                             StructuralModel)

    model = StructuralModel(
        materials=[ConcreteMaterial(id="C4000", fc=27_600.0, E=24.9e6, unit_weight=23.6),
                   RebarMaterial(id="G60", fy=414_000.0, fu=620_000.0, E=2.0e8, unit_weight=77.0)],
        sections=[RectangularSection(id="COL", b=0.45, h=0.45, material_id="C4000", rebar_material_id="G60", cover=0.04),
                  GeneralSection(id="GEN", material_id="G60", A=0.01, I3=1e-4, I2=5e-5, J=1e-5, As2=0.008, As3=0.007)],
    )
    proj = Project(model=model, units="kN, m")
    # The record shares the model's material object: it must still be converted once
    proj.design_results["D"] = DesignResult(inputs=DesignInputs(
        design_code="ACI 318-25", materials=[model.materials[0]], sections=[model.sections[0].model_copy()],
        allowable_bearing_pressure=150.0, footing_cover=0.075))
    proj.convert_units("kip, in")

    concrete, rebar = proj.model.materials
    col, gen = proj.model.sections
    assert concrete.fc == pytest.approx(4.0030, abs=1e-4)                 # ksi
    assert concrete.unit_weight * 1728.0 * 1000.0 == pytest.approx(150.24, abs=0.01)  # kip/in^3 -> pcf
    assert (rebar.fy, rebar.fu) == (pytest.approx(60.046, abs=1e-3), pytest.approx(89.924, abs=1e-3))
    assert col.cover == pytest.approx(1.5748, abs=1e-4)
    assert (gen.As2, gen.As3) == (pytest.approx(12.400, abs=1e-3), pytest.approx(10.850, abs=1e-3))  # in^2
    assert gen.I2 == pytest.approx(120.13, abs=0.01)                      # in^4
    inputs = proj.design_results["D"].inputs
    assert inputs.materials[0].fc == pytest.approx(4.0030, abs=1e-4)
    assert inputs.sections[0].cover == pytest.approx(1.5748, abs=1e-4)
    assert inputs.allowable_bearing_pressure * 144.0 == pytest.approx(3.1328, abs=1e-4)  # ksi -> ksf
    assert inputs.footing_cover == pytest.approx(2.9528, abs=1e-4)

    proj.convert_units("kN, m")
    assert proj.model.materials[0].fc == pytest.approx(27_600.0)
    assert proj.model.materials[0].unit_weight == pytest.approx(23.6)
    assert proj.design_results["D"].inputs.allowable_bearing_pressure == pytest.approx(150.0)


def test_convert_combination_reactions_and_forces():
    """Envelope combination_reactions and combination_forces convert along with primary results."""
    from struct_core.analysis_result import envelope_results
    from struct_core.structural_model import SpringElement

    proj = Project(units="kN, m")
    proj.model.nodes = [Node(id="1", x=0.0, y=0.0, z=0.0), Node(id="2", x=0.0, y=0.0, z=3.0)]
    proj.model.elements = [SpringElement(id="S1", start_node="1", end_node="2", kx=1000.0, ky=2000.0)]
    proj.model.load_cases = [
        LoadCase(id="DEAD", element_loads=[DistributedLoad(element_id="S1", wy=-10.0, wy_end=-20.0)])
    ]
    r1 = AnalysisResult(
        analysis_case_id="C1",
        node_results={"1": NodeResult(node_id="1", reaction=NodeReaction(fz=100.0, my=30.0))},
        element_results={"S1": ElementResult(element_id="S1", forces=[BeamSectionForce(station=0.0, P=-100.0, M3=30.0)])},
    )
    r2 = AnalysisResult(
        analysis_case_id="C2",
        node_results={"1": NodeResult(node_id="1", reaction=NodeReaction(fz=60.0, my=80.0))},
        element_results={"S1": ElementResult(element_id="S1", forces=[BeamSectionForce(station=0.0, P=-60.0, M3=80.0)])},
    )
    env = envelope_results([r1, r2], output_case_id="ENV")
    assert set(env.node_results["1"].combination_reactions) == {"C1", "C2"}
    proj.analysis_results["ENV"] = env

    f_force = conversion_factor("kN, m", "kip, ft", "force")
    f_mom = conversion_factor("kN, m", "kip, ft", "moment")
    f_line = conversion_factor("kN, m", "kip, ft", "line_load")
    proj.convert_units("kip, ft")

    assert proj.model.elements[0].kx == pytest.approx(1000.0 * f_line)
    assert proj.model.load_cases[0].element_loads[0].wy_end == pytest.approx(-20.0 * f_line)
    comb_reac = proj.analysis_results["ENV"].node_results["1"].combination_reactions["C2"]
    assert comb_reac.fz == pytest.approx(60.0 * f_force)
    assert comb_reac.my == pytest.approx(80.0 * f_mom)
    comb_force = proj.analysis_results["ENV"].element_results["S1"].combination_forces["C2"][0]
    assert comb_force.P == pytest.approx(-60.0 * f_force)
    assert comb_force.M3 == pytest.approx(80.0 * f_mom)


def test_mass_and_mass_density_conversion_factor():
    """F7 regression test: mass and mass_density conversion factor between SI and imperial."""
    # 2400 kg/m^3 to slug/in^3
    f_density = conversion_factor("kN, m", "kip, in", "mass_density")
    assert 2400.0 * f_density == pytest.approx(0.0026949, rel=1e-4)

    # 1000 kg to slug
    f_mass = conversion_factor("kN, m", "kip, in", "mass")
    assert 1000.0 * f_mass == pytest.approx(68.52176, rel=1e-4)


def test_project_metadata_units_assignment_syncs_model():
    """F14.2: Direct assignment to project.metadata.units syncs project.model.units."""
    proj = Project(units="kN, m")
    assert proj.metadata.units == parse_units("kN, m")
    assert proj.model.units == parse_units("kN, m")

    proj.metadata.units = parse_units("kip, in")
    assert proj.metadata.units == parse_units("kip, in")
    assert proj.model.units == parse_units("kip, in")

