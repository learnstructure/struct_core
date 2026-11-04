"""
Unit tests for material schemas.
"""

import pytest
from pydantic import TypeAdapter, ValidationError
from struct_core.structural_model.materials import (
    BilinearMaterial,
    ConcreteMaterial,
    ElasticMaterial,
    Material,
    RebarMaterial,
)


def test_elastic_material_creation():
    mat = ElasticMaterial(id="Steel", E=200e9, nu=0.3, rho=7850)
    assert mat.id == "Steel"
    assert mat.type == "elastic"
    assert mat.E == 200e9
    assert mat.rho == 7850


def test_bilinear_material_creation():
    mat = BilinearMaterial(id="Rebar", E=200e9, Et=2e9, fy=400e6)
    assert mat.id == "Rebar"
    assert mat.type == "bilinear"
    assert mat.fy == 400e6


def test_invalid_elastic_modulus():
    with pytest.raises(ValidationError):
        ElasticMaterial(id="Invalid", E=-200e9)


def test_material_polymorphic_parsing():
    adapter = TypeAdapter(Material)

    elastic_data = {"type": "elastic", "id": 1, "E": 30e9}
    parsed_elastic = adapter.validate_python(elastic_data)
    assert isinstance(parsed_elastic, ElasticMaterial)
    assert parsed_elastic.E == 30e9

    bilinear_data = {"type": "bilinear", "id": 2, "E": 200e9, "Et": 1e9, "fy": 250e6}
    parsed_bilinear = adapter.validate_python(bilinear_data)
    assert isinstance(parsed_bilinear, BilinearMaterial)
    assert parsed_bilinear.fy == 250e6


def test_concrete_and_rebar_materials():
    adapter = TypeAdapter(Material)
    concrete = adapter.validate_python({"type": "concrete", "id": "C4000", "fc": 27_600.0, "E": 24.9e6, "unit_weight": 23.6})
    rebar = adapter.validate_python({"type": "rebar", "id": "G60", "fy": 414_000.0, "fu": 620_000.0, "E": 2.0e8})
    assert isinstance(concrete, ConcreteMaterial) and isinstance(concrete, ElasticMaterial)  # analysed as elastic
    assert isinstance(rebar, RebarMaterial) and isinstance(rebar, ElasticMaterial)
    assert (concrete.fc, concrete.nu) == (27_600.0, 0.2)  # concrete's Poisson ratio unless given
    assert (rebar.fy, rebar.fu, rebar.nu) == (414_000.0, 620_000.0, 0.3)
    with pytest.raises(ValidationError):
        ConcreteMaterial(id="NoStrength", E=24.9e6)  # f'c is required
    with pytest.raises(ValidationError):
        RebarMaterial(id="NoYield", E=2.0e8)  # fy is required
