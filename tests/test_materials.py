"""
Unit tests for material schemas.
"""

import pytest
from pydantic import TypeAdapter, ValidationError
from struct_core.materials import (
    BilinearMaterial,
    ElasticMaterial,
    Material,
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
