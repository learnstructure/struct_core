"""
Unit tests for support schemas.
"""

from struct_core.structural_model.supports import Support


def test_support_custom():
    sup = Support(node_id="N1", ux=True, uy=False, rz=False, kx=1e6)
    assert sup.node_id == "N1"
    assert sup.ux is True
    assert sup.uy is False
    assert sup.rz is False
    assert sup.kx == 1e6


def test_support_factories():
    pinned = Support.pinned(node_id=1)
    assert pinned.ux is True
    assert pinned.uy is True
    assert pinned.rz is False

    fixed = Support.fixed(node_id=2)
    assert fixed.ux is True
    assert fixed.uy is True
    assert fixed.rz is True

    roller_x = Support.roller_x(node_id=3)
    assert roller_x.ux is False
    assert roller_x.uy is True
    assert roller_x.rz is False
