"""
Unit tests for load schemas.
"""

from struct_core.structural_model.loads import (
    DistributedLoad,
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

