"""
Unit tests for load schemas.
"""

from struct_core.structural_model.loads import (
    DistributedLoad,
    ElementPointLoad,
    GroundMotion,
    LoadCase,
    LoadCaseFactor,
    LoadCombination,
    PointLoad,
)


def test_point_load():
    pload = PointLoad(node_id="N1", fy=-50.0, mz=10.0)
    assert pload.node_id == "N1"
    assert pload.fx == 0.0
    assert pload.fy == -50.0
    assert pload.mz == 10.0


def test_distributed_load():
    dload = DistributedLoad(element_id="E1", wy=-10.0, is_local=True)
    assert dload.element_id == "E1"
    assert dload.wy == -10.0
    assert dload.is_local is True


def test_ground_motion():
    gm = GroundMotion(id="ElCentro", dt=0.02, acc=[0.0, 0.01, 0.05, 0.02, 0.0])
    assert gm.id == "ElCentro"
    assert gm.dt == 0.02
    assert len(gm.acc) == 5


def test_load_case_and_combination():
    lc_dead = LoadCase(
        id="DL",
        name="Dead Load",
        point_loads=[PointLoad(node_id=1, fy=-100.0)],
    )
    lc_live = LoadCase(
        id="LL",
        name="Live Load",
        point_loads=[PointLoad(node_id=1, fy=-50.0)],
    )

    comb = LoadCombination(
        id="COMB1",
        name="1.2D + 1.6L",
        factors=[
            LoadCaseFactor(load_case_id=lc_dead.id, factor=1.2),
            LoadCaseFactor(load_case_id=lc_live.id, factor=1.6),
        ],
    )

    assert len(comb.factors) == 2
    assert comb.factors[0].factor == 1.2
    assert comb.factors[1].factor == 1.6


def test_area_load():
    from struct_core import AreaLoad
    aload = AreaLoad(
        id="Floor_L2",
        story_elevation=3.5,
        pressure=2.4,
        load_type="live",
        tributary_width=5.0,
    )
    assert aload.pressure == 2.4
    assert aload.tributary_width == 5.0
    assert aload.one_way is True

    lc = LoadCase(id="LL", name="Live Load", area_loads=[aload], include_self_weight=False)
    assert len(lc.area_loads) == 1
    assert lc.include_self_weight is False


def test_mass_source():
    from struct_core import MassSource, MassSourceFactor

    ms = MassSource(
        id="MS_SEISMIC",
        name="ASCE 7 Seismic Weight",
        include_element_mass=True,
        include_added_mass=True,
        lateral_only=False,
        factors=[
            MassSourceFactor(load_case_id="DEAD", factor=1.0),
            MassSourceFactor(load_case_id="LIVE", factor=0.25),
        ],
    )
    assert ms.id == "MS_SEISMIC"
    assert ms.include_element_mass is True
    assert len(ms.factors) == 2
    assert ms.factors[0].load_case_id == "DEAD"
    assert ms.factors[0].factor == 1.0
    assert ms.factors[1].factor == 0.25
    assert ms.lateral_only is False


def test_element_point_load():
    epl = ElementPointLoad(element_id="B1", position=0.4, fy=-25.0, mz=12.5, is_local=True)
    assert epl.element_id == "B1"
    assert epl.position == 0.4
    assert epl.fy == -25.0
    assert epl.mz == 12.5
    assert epl.is_local is True

    lc = LoadCase(id="POINT_TEST", element_point_loads=[epl])
    assert len(lc.element_point_loads) == 1
    assert lc.element_point_loads[0].element_id == "B1"


def test_partial_and_varying_distributed_load():
    import pytest
    from pydantic import ValidationError

    # Partial varying load
    dl = DistributedLoad(element_id="B1", wy=-10.0, wy_end=-20.0, start=0.2, end=0.8)
    assert dl.wy == -10.0
    assert dl.wy_end == -20.0
    assert dl.start == 0.2
    assert dl.end == 0.8

    # Invalid span: start >= end
    with pytest.raises(ValidationError):
        DistributedLoad(element_id="B1", wy=-10.0, start=0.6, end=0.4)

    # Invalid span: out of [0, 1]
    with pytest.raises(ValidationError):
        DistributedLoad(element_id="B1", wy=-10.0, start=-0.1, end=0.5)

    # Legacy w_start / w_end migration
    dl_legacy = DistributedLoad(element_id="B1", w_start=-5.0, w_end=-15.0)
    assert dl_legacy.wy == -5.0
    assert dl_legacy.wy_end == -15.0


