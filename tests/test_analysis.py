"""
Unit tests for analysis case schemas.
"""

from pydantic import TypeAdapter
from struct_core.structural_model.analysis import (
    AnalysisCase,
    LinearStaticAnalysis,
    ModalAnalysis,
    NonlinearStaticAnalysis,
    TimeHistoryAnalysis,
)


def test_linear_static_analysis():
    case = LinearStaticAnalysis(id="LS1", load_case_id="DL")
    assert case.id == "LS1"
    assert case.type == "linear_static"
    assert case.load_case_id == "DL"


def test_nonlinear_static_analysis():
    case = NonlinearStaticAnalysis(id="NLS1", load_case_id="DL", max_steps=20, tolerance=1e-5)
    assert case.id == "NLS1"
    assert case.type == "nonlinear_static"
    assert case.max_steps == 20
    assert case.tolerance == 1e-5


def test_modal_analysis():
    case = ModalAnalysis(id="MOD1", num_modes=6)
    assert case.id == "MOD1"
    assert case.type == "modal"
    assert case.num_modes == 6


def test_time_history_analysis():
    case = TimeHistoryAnalysis(id="TH1", ground_motion_id="EQ1", dt=0.01, total_time=10.0, damping_ratio=0.05)
    assert case.id == "TH1"
    assert case.type == "time_history"
    assert case.ground_motion_id == "EQ1"
    assert case.total_time == 10.0


def test_analysis_polymorphic_parsing():
    adapter = TypeAdapter(AnalysisCase)

    data = {"type": "modal", "id": "M1", "num_modes": 5}
    parsed = adapter.validate_python(data)
    assert isinstance(parsed, ModalAnalysis)
    assert parsed.num_modes == 5
