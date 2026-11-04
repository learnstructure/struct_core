"""
Unit tests for analysis_result, design_result, detailing_result, and full Project lifecycle serialization.
"""

import tempfile
from pathlib import Path

import pytest
from struct_core.analysis_result import (
    AnalysisResult,
    BeamSectionForce,
    ElementResult,
    NodeDisplacement,
    NodeResult,
)
from struct_core.design_result import CodeCheckResult, DesignResult, ElementDesignResult, FlexureDesignResult
from struct_core.detailing_result import (
    Bar,
    BarLayout,
    BarSchedule,
    BarScheduleItem,
    DetailingResult,
    ElementDetailingResult,
    RebarLayer,
)
from struct_core.project import Project
from struct_core.serialization import load_json, save_json


def test_analysis_result_schema():
    res = AnalysisResult(
        analysis_case_id="StaticCase1",
        node_results={
            1: NodeResult(node_id=1, displacement=NodeDisplacement(ux=0.001, uy=-0.005, rz=0.0002)),
        },
        element_results={
            101: ElementResult(
                element_id=101,
                forces=[BeamSectionForce(station=0.0, P=50.0, V2=12.5, V3=5.0, M2=15.0, M3=45.0, T=2.0)],
            )
        },
    )

    assert res.analysis_case_id == "StaticCase1"
    assert res.node_results[1].displacement.uy == -0.005
    assert res.element_results[101].forces[0].V2 == 12.5
    assert res.element_results[101].forces[0].M3 == 45.0
    assert res.element_results[101].forces[0].Vy == 12.5
    assert res.element_results[101].forces[0].Mz == 45.0


def test_design_result_schema():
    des = DesignResult(
        design_code="ACI 318-19",
        element_results={
            101: ElementDesignResult(
                element_id=101,
                member_type="beam",
                flexure=FlexureDesignResult(
                    required_steel_area=1.44,
                    provided_steel_area=1.58,
                    phi_mn=1800.0,
                    mu=1450.0,
                    dcr=0.806,
                    passed=True,
                ),
                code_checks=[
                    CodeCheckResult(
                        clause="ACI 318-19 §9.6.1",
                        demand=1450.0,
                        capacity=1800.0,
                        dcr=0.806,
                        passed=True,
                    )
                ],
                passed=True,
            )
        },
        governing_dcr=0.806,
        passed=True,
    )

    assert des.design_code == "ACI 318-19"
    assert des.element_results[101].flexure.dcr == 0.806
    assert des.element_results[101].passed is True


def test_detailing_result_schema():
    det = DetailingResult(
        element_results={
            101: ElementDetailingResult(
                element_id=101,
                member_type="beam",
                bar_layout=BarLayout(
                    bottom_layers=[
                        RebarLayer(depth=17.5, bars=[Bar(mark="1B1", size=8, count=2, length=240.0)])
                    ]
                ),
                bar_schedule=BarSchedule(
                    items=[
                        BarScheduleItem(
                            mark="1B1", bar_size=8, quantity=2, cut_length=240.0, total_length=480.0, weight=127.2
                        )
                    ],
                    total_weight=127.2,
                ),
            )
        }
    )

    assert len(det.element_results[101].bar_layout.bottom_layers) == 1
    assert det.element_results[101].bar_schedule.total_weight == 127.2


def test_full_project_lifecycle_serialization():
    proj = Project()
    proj.metadata.title = "Full Lifecycle Test Frame"

    # Add Analysis Result
    an_res = AnalysisResult(
        analysis_case_id="A1",
        node_results={1: NodeResult(node_id=1, displacement=NodeDisplacement(uy=-0.01))},
    )
    proj.analysis_results["A1"] = an_res

    # Add Design Result
    des_res = DesignResult(
        design_code="ACI 318-19",
        element_results={1: ElementDesignResult(element_id=1, governing_dcr=0.75, passed=True)},
    )
    proj.design_results["ACI318_Case"] = des_res

    # Add Detailing Result
    det_res = DetailingResult(
        element_results={1: ElementDetailingResult(element_id=1, member_type="beam")}
    )
    proj.detailing_results["ACI318_Detailing"] = det_res

    # Convenience properties test
    assert proj.analysis_result.analysis_case_id == "A1"
    assert proj.design_result.design_code == "ACI 318-19"
    assert proj.detailing_result is not None

    with tempfile.TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir) / "full_project.json")
        save_json(proj, path)

        loaded = load_json(Project, path)
        assert loaded.metadata.title == "Full Lifecycle Test Frame"
        assert "A1" in loaded.analysis_results
        # JSON round-trips convert int dict keys to strings; access via "1" after deserialization
        node_res = next(iter(loaded.analysis_results["A1"].node_results.values()))
        assert node_res.displacement.uy == -0.01
        assert "ACI318_Case" in loaded.design_results
        assert "ACI318_Detailing" in loaded.detailing_results


def test_superpose_results_spectral_case_adds_magnitude_in_governing_direction():
    """Sign-less spectral (RSA) cases add |gamma*E| with the sign of the static sum: G +/- E -> |G| + |E|."""
    from struct_core.analysis_result import superpose_results

    def _result(cid, m_i, m_j, ux):
        return AnalysisResult(
            analysis_case_id=cid,
            node_results={1: NodeResult(node_id=1, displacement=NodeDisplacement(ux=ux))},
            element_results={
                "B1": ElementResult(
                    element_id="B1",
                    forces=[BeamSectionForce(station=0.0, M3=m_i), BeamSectionForce(station=1.0, M3=m_j)],
                )
            },
        )

    cases = {"D": _result("D", -10.0, 5.0, 0.0), "E": _result("E", 4.0, 4.0, 0.02)}
    plus = superpose_results(cases, {"D": 1.2, "E": 1.0}, "1.2D+E", spectral_case_ids=["E"])
    minus = superpose_results(cases, {"D": 1.2, "E": -1.0}, "1.2D-E", spectral_case_ids=["E"])

    plus_mi, plus_mj = (s.M3 for s in plus.element_results["B1"].forces)
    assert plus_mi == -16.0
    assert plus_mj == 10.0
    assert plus.node_results[1].displacement.ux == 0.02

    minus_mi, minus_mj = (s.M3 for s in minus.element_results["B1"].forces)
    assert minus_mi == -16.0
    assert minus_mj == 10.0
    assert minus.node_results[1].displacement.ux == -0.02

    linear = superpose_results(cases, {"D": 1.2, "E": 1.0}, "linear")
    assert [s.M3 for s in linear.element_results["B1"].forces] == [-8.0, 10.0]


def test_frame_topology_classifies_members_and_stories():
    from struct_core import (BeamElement, Node, StructuralModel, classify_frame_members, frame_stories,
                             vertical_axis)

    nodes = [Node(id=1, x=0, y=0), Node(id=2, x=5, y=0), Node(id=3, x=0, y=4), Node(id=4, x=5, y=4),
             Node(id=5, x=0, y=7.5), Node(id=6, x=5, y=7.5)]
    elements = [
        BeamElement(id="C1", start_node=1, end_node=3, section_id="S"),
        BeamElement(id="C2", start_node=4, end_node=2, section_id="S"),  # defined top-down
        BeamElement(id="C3", start_node=3, end_node=5, section_id="S"),
        BeamElement(id="C4", start_node=4, end_node=6, section_id="S"),
        BeamElement(id="B1", start_node=3, end_node=4, section_id="S"),
        BeamElement(id="B2", start_node=5, end_node=6, section_id="S"),
        BeamElement(id="D1", start_node=1, end_node=4, section_id="S"),
    ]
    model = StructuralModel.model_construct(nodes=nodes, elements=elements)
    assert vertical_axis(model) == "y"
    roles = classify_frame_members(model)
    assert roles == {"C1": "column", "C2": "column", "C3": "column", "C4": "column",
                     "B1": "beam", "B2": "beam", "D1": "brace"}
    stories = frame_stories(model)
    assert [(s.bottom, s.top) for s in stories] == [(0, 4), (4, 7.5)]
    assert sorted(stories[0].column_ids) == ["C1", "C2"] and stories[1].height == pytest.approx(3.5)


def test_project_records_seismic_design_basis():
    from struct_core import Project, SeismicDesignBasis

    basis = SeismicDesignBasis(system="rc_smf", r_factor=8.0, omega_0=3.0, cd=5.5, procedure="elf",
                               lateral_case_ids=["EQ_X"], directions=["x"])
    project = Project(seismic_basis=basis)
    restored = Project.model_validate_json(project.model_dump_json())
    assert restored.seismic_basis == basis
