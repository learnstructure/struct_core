"""Tests of the shell schemas: ShellSection, ShellElement, ShellLoad, shell results, validation, units, and
superposition."""

import math

import numpy as np
import pytest
from pydantic import ValidationError

from struct_core import (
    AnalysisResult,
    ConcreteMaterial,
    LoadCase,
    Node,
    Project,
    RectangularSection,
    BeamElement,
    ShellElement,
    ShellElementResult,
    ShellForces,
    ShellLoad,
    ShellNodeForces,
    ShellSection,
    StructuralModel,
    Support,
    convert_project_units,
    validate_structural_model,
)
from struct_core.analysis_result import envelope_results, superpose_results
from struct_core.geometry import model_shell_axes


def slab_model(**shell_kw) -> StructuralModel:
    """A 2 x 1 m slab of two square elements on four corner supports, in kN, m."""
    nodes = [Node(id=i + 1, x=x, y=y, z=0.0) for i, (x, y) in enumerate(
        [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)])]
    return StructuralModel(
        units="kN, m",
        nodes=nodes,
        materials=[ConcreteMaterial(id="C", E=25e6, fc=30e3, unit_weight=24.0)],
        shell_sections=[ShellSection(id="S200", material_id="C", thickness=0.2)],
        shell_elements=[
            ShellElement(id="A1", node_ids=[1, 2, 5, 4], section_id="S200", **shell_kw),
            ShellElement(id="A2", node_ids=[2, 3, 6, 5], section_id="S200", **shell_kw),
        ],
        supports=[Support(node_id=n, ux=True, uy=True, uz=True) for n in (1, 3, 4, 6)],
        load_cases=[LoadCase(id="DEAD", load_type="dead",
                             shell_loads=[ShellLoad(element_ids=["A1", "A2"], pressure=-2.0, direction="z")])],
    )


# ── Schemas ─────────────────────────────────────────────────────────────────────────────────────────────────


def test_shell_section_defaults_follow_csi_recommendations():
    s = ShellSection(id="S", material_id="C", thickness=0.25)
    assert (s.behavior, s.plate_theory) == ("shell", "thick")
    assert s.effective_bending_thickness == 0.25
    assert ShellSection(id="S", material_id="C", thickness=0.25, bending_thickness=0.2).effective_bending_thickness == 0.2
    with pytest.raises(ValidationError):
        ShellSection(id="S", material_id="C", thickness=0.0)
    with pytest.raises(ValidationError):
        ShellSection(id="S", material_id="C", thickness=0.2, behavior="plane")
    with pytest.raises(ValidationError):  # reinforcement stays off the shell section until slab design
        ShellSection(id="S", material_id="C", thickness=0.2, cover=0.02)


@pytest.mark.parametrize("nodes", [[1, 2], [1, 2, 3, 4, 5], [1, 2, 2, 4]])
def test_shell_element_needs_three_or_four_distinct_nodes(nodes):
    with pytest.raises(ValidationError):
        ShellElement(id="E", node_ids=nodes, section_id="S")


def test_shell_element_reference_vector_must_not_be_zero():
    with pytest.raises(ValidationError, match="must not be zero"):
        ShellElement(id="E", node_ids=[1, 2, 3], section_id="S", reference_vector=(0, 0, 0))


def test_shell_load_direction_and_elements():
    with pytest.raises(ValidationError):
        ShellLoad(element_ids=[], pressure=1.0, direction="z")
    with pytest.raises(ValidationError):
        ShellLoad(element_ids=["A"], pressure=1.0, direction="-z")  # the sign belongs to the pressure


def test_shell_lists_are_separate_from_frames_and_round_trip_json():
    model = slab_model()
    assert model.elements == [] and model.sections == []
    again = StructuralModel.model_validate_json(model.model_dump_json())
    assert again.shell_elements == model.shell_elements
    assert again.load_cases[0].shell_loads == model.load_cases[0].shell_loads


def test_section_and_material_lookups_resolve_shells():
    model = slab_model()
    assert model.section_of("A1").thickness == 0.2
    assert model.section_of(model.shell_elements[0]).id == "S200"
    assert model.material_of(model.shell_elements[0]).id == "C"
    assert model.get_shell_element("A2").node_ids == [2, 3, 6, 5]


def test_model_shell_axes_uses_the_canonical_function():
    axes = model_shell_axes(slab_model(axis_angle=90.0))
    assert np.allclose(axes["A1"][0], [0, 1, 0]) and np.allclose(axes["A1"][2], [0, 0, 1])


# ── Validation ──────────────────────────────────────────────────────────────────────────────────────────────


def test_valid_slab_has_no_errors():
    assert validate_structural_model(slab_model(), raise_error=False) == []


def test_missing_references_and_duplicate_ids():
    model = slab_model()
    model.sections.append(RectangularSection(id="B", material_id="C", b=0.3, h=0.5))
    model.elements.append(BeamElement(id="A1", start_node=1, end_node=2, section_id="B"))
    model.shell_elements.append(ShellElement(id="A3", node_ids=[1, 2, 99], section_id="B"))
    model.shell_sections.append(ShellSection(id="B", material_id="nope", thickness=0.1))
    model.load_cases[0].shell_loads.append(ShellLoad(element_ids=["A9"], pressure=1.0, direction="local_3"))
    errors = validate_structural_model(model, raise_error=False)
    text = "\n".join(errors)
    assert "Duplicate Element ID found: 'A1' (shell element)" in text
    assert "Duplicate Section ID found: 'B' (shell section)" in text
    assert "Shell section 'B' references missing material_id 'nope'" in text
    assert "Shell element 'A3' references missing node(s) [99]" in text
    assert "references missing shell element(s) ['A9']" in text


def test_frame_section_on_shell_element_gets_a_hint():
    model = slab_model()
    model.sections.append(RectangularSection(id="B", material_id="C", b=0.3, h=0.5))
    model.shell_elements[0].section_id = "B"
    errors = validate_structural_model(model, raise_error=False)
    assert any("a frame section; shell elements need a shell section" in e for e in errors)


def test_shape_errors_are_validation_errors_and_warnings_are_not():
    model = slab_model()
    model.nodes[4].x, model.nodes[4].y = 0.2, 0.2  # node 5 inside A1: a re-entrant corner (above 180 degrees)
    errors = validate_structural_model(model, raise_error=False)
    assert any("A1" in e and "inside angle" in e and "§10.2.1" in e for e in errors)
    model = slab_model()
    model.nodes[4].x = 1.35  # skewed, but every inside angle below 180 degrees
    assert validate_structural_model(model, raise_error=False) == []


def test_reference_vector_parallel_to_normal_is_a_validation_error():
    model = slab_model(reference_vector=(0.0, 0.0, 1.0))
    errors = validate_structural_model(model, raise_error=False)
    assert any("parallel to local axis 3" in e for e in errors)


# ── Units ───────────────────────────────────────────────────────────────────────────────────────────────────


def shell_result(case_id, scale=1.0, node_scale=1.0):
    f = ShellForces(F11=1.0 * scale, F22=2.0 * scale, F12=0.5 * scale, M11=3.0 * scale, M22=-1.0 * scale,
                    M12=0.2 * scale, V13=0.4 * scale, V23=-0.6 * scale)
    return AnalysisResult(
        analysis_case_id=case_id,
        shell_results={"A1": ShellElementResult(element_id="A1", gauss_points=[f] * 4, corners=[f] * 4)},
        shell_node_results={2: [ShellNodeForces(node_id=2, element_ids=["A1", "A2"], normal=(0, 0, 1),
                                                axis_1=(1, 0, 0), forces=f.model_copy(update={"M11": 3.0 * node_scale}))]},
    )


def test_unit_conversion_of_shell_sections_loads_and_results():
    project = Project(model=slab_model(), units="kN, m")
    project.analysis_results["DEAD"] = shell_result("DEAD")
    convert_project_units(project, "kip, in")
    m_to_in = 1 / 0.0254
    kn_to_kip = 1 / 4.4482216152605
    assert math.isclose(project.model.shell_sections[0].thickness, 0.2 * m_to_in, rel_tol=1e-9)
    assert math.isclose(project.model.load_cases[0].shell_loads[0].pressure, -2.0 * kn_to_kip / m_to_in ** 2,
                        rel_tol=1e-9)
    r = project.analysis_results["DEAD"]
    gp = r.shell_results["A1"].gauss_points[0]
    assert math.isclose(gp.F11, 1.0 * kn_to_kip / m_to_in, rel_tol=1e-9)   # force per length
    assert math.isclose(gp.M11, 3.0 * kn_to_kip, rel_tol=1e-9)             # moment per length = force
    assert math.isclose(gp.V23, -0.6 * kn_to_kip / m_to_in, rel_tol=1e-9)
    assert math.isclose(r.shell_node_results[2][0].forces.M11, 3.0 * kn_to_kip, rel_tol=1e-9)


# ── Superposition and envelopes ─────────────────────────────────────────────────────────────────────────────


def test_combination_superposes_shell_results():
    cases = {"D": shell_result("D"), "L": shell_result("L", scale=2.0, node_scale=2.0)}
    combo = superpose_results(cases, {"D": 1.2, "L": 1.6}, "C1")
    gp = combo.shell_results["A1"].gauss_points[2]
    assert math.isclose(gp.M11, 1.2 * 3.0 + 1.6 * 6.0)
    assert math.isclose(gp.V23, 1.2 * -0.6 + 1.6 * -1.2)
    assert math.isclose(combo.shell_node_results[2][0].forces.M11, 1.2 * 3.0 + 1.6 * 6.0)
    assert combo.shell_node_results[2][0].element_ids == ["A1", "A2"]


def test_spectral_case_adds_magnitude_to_moments():
    cases = {"D": shell_result("D"), "E": shell_result("E", scale=-1.0, node_scale=-1.0)}
    combo = superpose_results(cases, {"D": 1.0, "E": 1.0}, "C2", spectral_case_ids=["E"])
    gp = combo.shell_results["A1"].gauss_points[0]
    assert math.isclose(gp.M11, 6.0) and math.isclose(gp.M22, -2.0)


def test_missing_shell_result_in_a_case_is_refused():
    cases = {"D": shell_result("D"), "L": AnalysisResult(analysis_case_id="L")}
    with pytest.raises(ValueError, match="shell element 'A1' missing in case 'L'"):
        superpose_results(cases, {"D": 1.0, "L": 1.0}, "C")


def test_envelope_keeps_largest_magnitudes_and_concurrent_corners():
    a = superpose_results({"D": shell_result("D")}, {"D": 1.0}, "C1")
    b = superpose_results({"D": shell_result("D", scale=-2.0)}, {"D": 1.0}, "C2")
    env = envelope_results([a, b])
    sr = env.shell_results["A1"]
    assert math.isclose(sr.corners[0].M11, -6.0) and math.isclose(sr.corners[0].F22, -4.0)
    assert set(sr.combination_corners) == {"C1", "C2"}
    assert math.isclose(sr.combination_corners["C1"][0].M11, 3.0)
