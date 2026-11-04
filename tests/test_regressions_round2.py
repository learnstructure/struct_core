"""
Round 2 regression tests covering fixed issues and invariants across struct_core and related libraries.
"""

import pytest
from pydantic import ValidationError

from struct_core import (
    Node,
    Project,
    StructuralModel,
    Support,
    Units,
    conversion_factor,
    convert_project_units,
    parse_units,
    validate_structural_model,
)
from struct_core.analysis_result import (
    AnalysisResult,
    BeamSectionForce,
    ElementResult,
    NodeDisplacement,
    TimeHistoryResult,
    TimeStepResult,
    superpose_results,
)
from struct_core.structural_model import (
    BeamElement,
    ElasticMaterial,
    GeneralSection,
    LoadCase,
    LoadCaseFactor,
    LoadCombination,
    RectangularSection,
)
from struct_load import LoadGenerator


def test_unit_conversion_regressions():
    """Verify convert_project_units correctly scales rho, nodal mass, TH displacements, while preserving stations."""
    m = ElasticMaterial(id="CONC", E=30e6, rho=2400.0)
    sec = RectangularSection(id="BEAM", material_id="CONC", b=0.3, h=0.5)
    n1 = Node(id=1, x=0, y=0, mass=1000.0)
    n2 = Node(id=2, x=5, y=0)
    el = BeamElement(id=1, start_node=1, end_node=2, section_id="BEAM")

    th = TimeHistoryResult(
        dt=0.02,
        time_steps=[
            TimeStepResult(time=0.0, displacements={1: NodeDisplacement(ux=0.01, uy=0.0)}),
        ],
    )
    res = AnalysisResult(
        analysis_case_id="TH",
        element_results={
            1: ElementResult(
                element_id=1,
                forces=[
                    BeamSectionForce(station=0.0, P=10.0),
                    BeamSectionForce(station=0.5, P=10.0),
                    BeamSectionForce(station=1.0, P=10.0),
                ],
            )
        },
        time_history_result=th,
    )

    proj = Project(
        model=StructuralModel(
            dimension="2D",
            units="kN, m",
            nodes=[n1, n2],
            elements=[el],
            materials=[m],
            sections=[sec],
        ),
        analysis_results={"TH": res},
    )

    proj_converted = convert_project_units(proj, "kip, in")
    c_mat = proj_converted.model.materials[0]
    c_node = proj_converted.model.nodes[0]
    c_el_res = proj_converted.analysis_results["TH"].element_results[1]
    c_th = proj_converted.analysis_results["TH"].time_history_result

    # rho: 2400 kg/m^3 -> 0.0026949 slug/in^3 (within 1e-4 relative tolerance)
    assert c_mat.rho == pytest.approx(0.0026949, rel=1e-4)

    # Node.mass: 1000 kg -> 68.522 slugs (within 1e-4 relative tolerance)
    assert c_node.mass == pytest.approx(68.522, rel=1e-4)

    # stations stay [0, 0.5, 1]
    assert [f.station for f in c_el_res.forces] == [0.0, 0.5, 1.0]

    # Time-history displacement: 0.01 m -> 0.3937 in (within 1e-4 relative tolerance)
    assert c_th.time_steps[0].displacements[1].ux == pytest.approx(0.3937, rel=1e-3)


def test_parse_units_regressions():
    """Verify parse_units error handling, mass preservation, metric defaults, and dict equality."""
    with pytest.raises(ValueError, match="Unknown unit token 'furlong'"):
        parse_units("kN, furlong")

    u_lb = parse_units("lbf, in, lb")
    assert u_lb.mass == "lb"

    u_nmm = parse_units("N, mm")
    assert u_nmm.mass == "tonne"

    u_nmm_sc = parse_units("N, mm, s, C")
    assert u_nmm_sc.mass == "tonne"

    u_dict = parse_units({"force": "kip", "length": "in"})
    u_str = parse_units("kip, in")
    assert u_dict == u_str


def test_validation_regressions():
    """Verify structural model validation catches duplicate supports, missing cases, unconstrained models, and invalid 3D sections."""
    # 1. Duplicate supports reported
    m_dup = StructuralModel(
        dimension="2D",
        units="kN, m",
        nodes=[Node(id=1, x=0, y=0), Node(id=2, x=5, y=0)],
        supports=[Support(node_id=1, ux=True), Support(node_id=1, uy=True)],
    )
    errs_dup = validate_structural_model(m_dup, raise_error=False)
    assert any("Duplicate support defined on Node '1'" in err for err in errs_dup)

    # 2. Combination naming missing case reported
    m_missing = StructuralModel(
        dimension="2D",
        units="kN, m",
        nodes=[Node(id=1, x=0, y=0), Node(id=2, x=5, y=0)],
        supports=[Support(node_id=1, ux=True)],
        load_combinations=[
            LoadCombination(
                id="COMB1",
                factors=[LoadCaseFactor(load_case_id="NONEXISTENT", factor=1.2)],
            )
        ],
    )
    errs_missing = validate_structural_model(m_missing, raise_error=False)
    assert any("LoadCombination 'COMB1' references missing load_case_id 'NONEXISTENT'" in err for err in errs_missing)

    # 3. Model with no supports reported
    m_no_supp = StructuralModel(
        dimension="2D",
        units="kN, m",
        nodes=[Node(id=1, x=0, y=0), Node(id=2, x=5, y=0)],
        supports=[],
    )
    errs_no_supp = validate_structural_model(m_no_supp, raise_error=False)
    assert any("no supports" in err for err in errs_no_supp)

    # 4. 3D GeneralSection without I2/J is refused
    mat = ElasticMaterial(id="M", E=200e6)
    sec_3d_no_i2 = GeneralSection(id="GS", material_id="M", A=0.01, I3=1e-4)
    m_3d_sec = StructuralModel(
        dimension="3D",
        units="kN, m",
        nodes=[Node(id=1, x=0, y=0, z=0), Node(id=2, x=0, y=0, z=3)],
        elements=[BeamElement(id=1, start_node=1, end_node=2, section_id="GS")],
        materials=[mat],
        sections=[sec_3d_no_i2],
        supports=[Support(node_id=1, ux=True, uy=True, uz=True, rx=True, ry=True, rz=True)],
    )
    errs_3d = validate_structural_model(m_3d_sec, raise_error=False)
    assert any("requires positive I2" in err for err in errs_3d)
    assert any("requires positive J" in err for err in errs_3d)


def test_spectral_superposition_combination():
    """Verify spectral combination rule: D = (P -100, M 40), E = (P 80, M 50), 0.9D ∓ E gives (-170, 86) and (-10, 86)."""
    res_D = AnalysisResult(
        analysis_case_id="D",
        element_results={
            "B": ElementResult(
                element_id="B",
                forces=[BeamSectionForce(station=0.0, P=-100.0, M3=40.0)],
            )
        },
    )
    res_E = AnalysisResult(
        analysis_case_id="E",
        element_results={
            "B": ElementResult(
                element_id="B",
                forces=[BeamSectionForce(station=0.0, P=80.0, M3=50.0)],
            )
        },
    )

    case_results = {"D": res_D, "E": res_E}

    comb_plus = superpose_results(
        case_results,
        factors={"D": 0.9, "E": 1.0},
        output_case_id="0.9D+E",
        spectral_case_ids=["E"],
    )
    comb_minus = superpose_results(
        case_results,
        factors={"D": 0.9, "E": -1.0},
        output_case_id="0.9D-E",
        spectral_case_ids=["E"],
    )

    f_plus = comb_plus.element_results["B"].forces[0]
    f_minus = comb_minus.element_results["B"].forces[0]

    assert f_plus.P == pytest.approx(-170.0)
    assert f_plus.M3 == pytest.approx(86.0)

    assert f_minus.P == pytest.approx(-10.0)
    assert f_minus.M3 == pytest.approx(86.0)


def test_superposition_different_station_counts_raises():
    """Verify superpose_results raises ValueError when elements have different station counts."""
    res1 = AnalysisResult(
        analysis_case_id="C1",
        element_results={
            "B": ElementResult(
                element_id="B",
                forces=[
                    BeamSectionForce(station=0.0, P=10.0),
                    BeamSectionForce(station=1.0, P=10.0),
                ],
            )
        },
    )
    res2 = AnalysisResult(
        analysis_case_id="C2",
        element_results={
            "B": ElementResult(
                element_id="B",
                forces=[
                    BeamSectionForce(station=0.0, P=10.0),
                    BeamSectionForce(station=0.5, P=10.0),
                    BeamSectionForce(station=1.0, P=10.0),
                ],
            )
        },
    )

    with pytest.raises(ValueError, match="station count mismatch"):
        superpose_results({"C1": res1, "C2": res2}, {"C1": 1.0, "C2": 1.0}, "COMB")


def test_load_case_type_validation():
    """Verify LoadCase rejects invalid load types."""
    with pytest.raises(ValidationError):
        LoadCase(id="D", load_type="Deadd")


def test_load_classification_and_generator():
    """Verify LoadGenerator classifies super_dead, storage_live, duplicate live, and named Gravity, while rejecting unclassified Equipment."""
    proj = Project(
        model=StructuralModel(
            dimension="2D",
            units="kN, m",
            nodes=[Node(id=1, x=0, y=0), Node(id=2, x=5, y=0)],
            supports=[Support(node_id=1, ux=True, uy=True, rz=True)],
            load_cases=[
                LoadCase(id="D", load_type="dead"),
                LoadCase(id="SD", load_type="super_dead"),
                LoadCase(id="L_store", load_type="storage_live"),
                LoadCase(id="L2", load_type="live"),
                LoadCase(id="Gravity", load_type="live"),
            ],
        )
    )

    gen = LoadGenerator(units="kN, m")
    combs = gen.generate_combinations(proj)
    comb_dict = {c.id: {f.load_case_id: f.factor for f in c.factors} for c in combs}

    # 1.4D should factor D and SD
    assert "COMB_1.4D" in comb_dict
    assert comb_dict["COMB_1.4D"]["D"] == 1.4
    assert comb_dict["COMB_1.4D"]["SD"] == 1.4

    # 1.2D + 1.6L should factor D, SD, L_store, L2, and Gravity
    assert "COMB_1.2D+1.6L" in comb_dict
    c12 = comb_dict["COMB_1.2D+1.6L"]
    assert c12["D"] == 1.2
    assert c12["SD"] == 1.2
    assert c12["L_store"] == 1.6
    assert c12["L2"] == 1.6
    assert c12["Gravity"] == 1.6

    # Equipment without a load_type raises ValueError
    proj_bad = Project(
        model=StructuralModel(
            dimension="2D",
            units="kN, m",
            nodes=[Node(id=1, x=0, y=0), Node(id=2, x=5, y=0)],
            supports=[Support(node_id=1, ux=True, uy=True, rz=True)],
            load_cases=[
                LoadCase(id="Equipment"),
            ],
        )
    )
    with pytest.raises(ValueError, match="Unable to determine load type for load case id='Equipment'"):
        gen.generate_combinations(proj_bad)

