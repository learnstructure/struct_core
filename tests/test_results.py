"""
Unit tests for analysis_result, design_result, detailing_result, and full Project lifecycle serialization.
"""

import tempfile
from pathlib import Path
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
                forces=[BeamSectionForce(station=0.0, P=50.0, Vy=12.5, Mz=45.0)],
            )
        },
    )

    assert res.analysis_case_id == "StaticCase1"
    assert res.node_results[1].displacement.uy == -0.005
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
